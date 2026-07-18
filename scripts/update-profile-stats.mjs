import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const username = process.env.PROFILE_USERNAME ?? 'loulanyue';
const token = process.env.GITHUB_TOKEN;
const checkOnly = process.argv.includes('--check');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const bannerPath = path.join(root, 'assets', 'profile-terminal.svg');
const featuredPath = path.join(root, 'assets', 'featured-systems.svg');
const featuredRepositories = [
  'spec-kit-zh',
  'dream-xi-ai',
  'awesome-claude-notes',
  'interview-notes',
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

function replaceTextById(source, id, value) {
  const pattern = new RegExp(`(<text\\b[^>]*\\bid="${id}"[^>]*>)[^<]*(</text>)`);
  if (!pattern.test(source)) {
    throw new Error(`Telemetry target not found: ${id}`);
  }
  return source.replace(pattern, `$1${value}$2`);
}

const [projects, profile, currentBanner, currentFeatured] = await Promise.all([
  getOwnedProjects(),
  request(`https://api.github.com/users/${username}`),
  readFile(bannerPath, 'utf8'),
  readFile(featuredPath, 'utf8'),
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

let nextBanner = currentBanner;
nextBanner = replaceTextById(nextBanner, 'total-stars', formattedStars);
nextBanner = replaceTextById(nextBanner, 'project-count', String(projectCount));
nextBanner = replaceTextById(nextBanner, 'follower-count', formattedFollowers);

let nextFeatured = currentFeatured;
for (const name of featuredRepositories) {
  const stars = repositoryByName.get(name).stargazers_count.toLocaleString('en-US');
  nextFeatured = replaceTextById(nextFeatured, `stars-${name}`, `★ ${stars}`);
}

const changedFiles = [
  { path: bannerPath, current: currentBanner, next: nextBanner },
  { path: featuredPath, current: currentFeatured, next: nextFeatured },
].filter((file) => file.current !== file.next);

if (changedFiles.length === 0) {
  console.log(`Profile telemetry is current: ${formattedStars} stars across ${projectCount} projects.`);
  process.exit(0);
}

if (checkOnly) {
  throw new Error(
    `Profile telemetry is stale. Expected ${formattedStars} stars across ${projectCount} projects.`,
  );
}

await Promise.all(changedFiles.map((file) => writeFile(file.path, file.next)));
console.log(
  `Updated ${changedFiles.length} profile asset(s): ${formattedStars} stars across ${projectCount} projects.`,
);
