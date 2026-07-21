import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const username = process.env.PROFILE_USERNAME ?? 'loulanyue';
const token = process.env.GITHUB_TOKEN;
const checkOnly = process.argv.includes('--check');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const bannerPath = path.join(root, 'assets', 'profile-terminal.svg');
const featuredPath = path.join(root, 'assets', 'featured-systems.svg');
const upstreamPath = path.join(root, 'assets', 'upstream-contributions.svg');

const featuredRepositories = [
  'spec-kit-zh',
  'dream-xi-ai',
  'awesome-claude-notes',
  'interview-notes',
];

const upstreamContributions = [
  { key: 'openclaw', owner: 'openclaw', repo: 'openclaw', pull: 111779 },
  { key: 'opencode', owner: 'anomalyco', repo: 'opencode', pull: 37726 },
  { key: 'langflow', owner: 'langflow-ai', repo: 'langflow', pull: 14153 },
  { key: 'llamafactory', owner: 'hiyouga', repo: 'LlamaFactory', pull: 10660 },
  { key: 'poetry', owner: 'python-poetry', repo: 'poetry', pull: 10983 },
  { key: 'mcptoolbox', owner: 'googleapis', repo: 'mcp-toolbox', pull: 3650 },
];

const headers = {
  Accept: 'application/vnd.github+json',
  'User-Agent': `${username}-profile-telemetry`,
  'X-GitHub-Api-Version': '2022-11-28',
};

if (token) headers.Authorization = `Bearer ${token}`;

async function request(url) {
  const response = await fetch(url, { headers });
  if (!response.ok) {
    throw new Error(`GitHub API ${response.status}: ${await response.text()}`);
  }
  return response.json();
}

async function getOwnedProjects() {
  const projects = [];
  for (let page = 1; ; page += 1) {
    const batch = await request(
      `https://api.github.com/users/${username}/repos?type=owner&sort=full_name&per_page=100&page=${page}`,
    );
    projects.push(...batch.filter((repository) => !repository.fork));
    if (batch.length < 100) break;
  }
  return projects;
}

async function getUpstreamPullRequests() {
  const query = encodeURIComponent(`is:pr author:${username} -user:${username}`);
  const first = await request(`https://api.github.com/search/issues?q=${query}&per_page=100&page=1`);
  const items = [...first.items];

  for (let page = 2; items.length < first.total_count && page <= 10; page += 1) {
    const next = await request(
      `https://api.github.com/search/issues?q=${query}&per_page=100&page=${page}`,
    );
    items.push(...next.items);
  }

  return { totalCount: first.total_count, items };
}

async function getContributionDetails() {
  return Promise.all(
    upstreamContributions.map(async (contribution) => {
      const base = `https://api.github.com/repos/${contribution.owner}/${contribution.repo}`;
      const [repository, pullRequest] = await Promise.all([
        request(base),
        request(`${base}/pulls/${contribution.pull}`),
      ]);
      return { ...contribution, repository, pullRequest };
    }),
  );
}

function replaceTextById(source, id, value) {
  const pattern = new RegExp(`(<text\\b[^>]*\\bid="${id}"[^>]*>)[^<]*(</text>)`);
  if (!pattern.test(source)) {
    throw new Error(`Telemetry target not found: ${id}`);
  }
  return source.replace(pattern, `$1${value}$2`);
}

function formatCompactNumber(value) {
  if (value < 1_000) return String(value);
  return `${(value / 1_000).toFixed(1).replace(/\\.0$/, '')}K`;
}

function pullRequestState(pullRequest) {
  if (pullRequest.merged_at) return 'MERGED';
  return pullRequest.state.toUpperCase();
}

const [
  projects,
  profile,
  upstreamSearch,
  contributionDetails,
  currentBanner,
  currentFeatured,
  currentUpstream,
] = await Promise.all([
  getOwnedProjects(),
  request(`https://api.github.com/users/${username}`),
  getUpstreamPullRequests(),
  getContributionDetails(),
  readFile(bannerPath, 'utf8'),
  readFile(featuredPath, 'utf8'),
  readFile(upstreamPath, 'utf8'),
]);

const repositoryByName = new Map(projects.map((repository) => [repository.name, repository]));
const missingFeatured = featuredRepositories.filter((name) => !repositoryByName.has(name));
if (missingFeatured.length > 0) {
  throw new Error(`Featured repositories not found: ${missingFeatured.join(', ')}`);
}

const totalStars = projects.reduce((sum, repository) => sum + repository.stargazers_count, 0);
const projectCount = projects.length;
const followerCount = profile.followers;
const formattedStars = totalStars.toLocaleString('en-US');
const formattedFollowers = followerCount.toLocaleString('en-US');
const refreshedOn = new Date().toISOString().slice(0, 10);

const upstreamMergedCount = upstreamSearch.items.filter(
  (item) => Boolean(item.pull_request?.merged_at),
).length;
const upstreamActiveCount = upstreamSearch.items.filter((item) => item.state === 'open').length;
const upstreamProjectCount = new Set(
  upstreamSearch.items.map((item) => item.repository_url.split('/repos/')[1]),
).size;

let nextBanner = currentBanner;
nextBanner = replaceTextById(nextBanner, 'total-stars', formattedStars);
nextBanner = replaceTextById(nextBanner, 'project-count', String(projectCount));
nextBanner = replaceTextById(nextBanner, 'follower-count', formattedFollowers);
nextBanner = replaceTextById(
  nextBanner,
  'last-updated-banner',
  `UPDATED ${refreshedOn} UTC`,
);

let nextFeatured = currentFeatured;
for (const name of featuredRepositories) {
  const stars = repositoryByName.get(name).stargazers_count.toLocaleString('en-US');
  nextFeatured = replaceTextById(nextFeatured, `stars-${name}`, `★ ${stars}`);
}
nextFeatured = replaceTextById(
  nextFeatured,
  'last-updated-featured',
  `LIVE STARS · UPDATED ${refreshedOn} UTC · 星标自动更新`,
);

let nextUpstream = currentUpstream;
nextUpstream = replaceTextById(
  nextUpstream,
  'upstream-pr-count',
  String(upstreamSearch.totalCount),
);
nextUpstream = replaceTextById(
  nextUpstream,
  'upstream-merged-count',
  String(upstreamMergedCount),
);
nextUpstream = replaceTextById(
  nextUpstream,
  'upstream-active-count',
  String(upstreamActiveCount),
);
nextUpstream = replaceTextById(
  nextUpstream,
  'upstream-project-count',
  String(upstreamProjectCount),
);
nextUpstream = replaceTextById(
  nextUpstream,
  'last-updated-upstream',
  `PR STATUS + STARS · UPDATED ${refreshedOn} UTC · 每日自动更新`,
);

for (const contribution of contributionDetails) {
  nextUpstream = replaceTextById(
    nextUpstream,
    `state-${contribution.key}`,
    pullRequestState(contribution.pullRequest),
  );
  nextUpstream = replaceTextById(
    nextUpstream,
    `repo-stars-${contribution.key}`,
    `★ ${formatCompactNumber(contribution.repository.stargazers_count)}`,
  );
}

const changedFiles = [
  { path: bannerPath, current: currentBanner, next: nextBanner },
  { path: featuredPath, current: currentFeatured, next: nextFeatured },
  { path: upstreamPath, current: currentUpstream, next: nextUpstream },
].filter((file) => file.current !== file.next);

const status = `${formattedStars} stars across ${projectCount} owned projects; ${upstreamSearch.totalCount} upstream PRs`;

if (changedFiles.length === 0) {
  console.log(`Profile telemetry is current: ${status}.`);
  process.exit(0);
}

if (checkOnly) {
  throw new Error(`Profile telemetry is stale. Expected ${status}.`);
}

await Promise.all(changedFiles.map((file) => writeFile(file.path, file.next)));
console.log(`Updated ${changedFiles.length} profile asset(s): ${status}.`);
