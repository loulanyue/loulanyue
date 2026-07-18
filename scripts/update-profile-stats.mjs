import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const username = process.env.PROFILE_USERNAME ?? 'loulanyue';
const token = process.env.GITHUB_TOKEN;
const checkOnly = process.argv.includes('--check');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const readmePath = path.join(root, 'README.md');

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

function badge(label, value, color, logo) {
  const encodedLabel = encodeURIComponent(label).replaceAll('%20', '_');
  const encodedValue = encodeURIComponent(value);
  return `https://img.shields.io/badge/${encodedLabel}-${encodedValue}-${color}?style=for-the-badge&labelColor=07111F&logo=${logo}&logoColor=FFFFFF`;
}

const [projects, profile] = await Promise.all([
  getOwnedProjects(),
  request(`https://api.github.com/users/${username}`),
]);

const totalStars = projects.reduce((sum, repository) => sum + repository.stargazers_count, 0);
const projectCount = projects.length;
const followerCount = profile.followers;
const formattedStars = totalStars.toLocaleString('en-US');
const formattedFollowers = followerCount.toLocaleString('en-US');

const telemetry = `<!-- PROFILE_STATS:START -->
<p align="center">
  <a href="https://github.com/${username}?tab=repositories"><img alt="Total stars across ${projectCount} owned public non-fork projects" src="${badge('TOTAL STARS', formattedStars, '00E5FF', 'github')}" /></a>
  <a href="https://github.com/${username}?tab=repositories"><img alt="${projectCount} owned public projects" src="${badge('PUBLIC PROJECTS', String(projectCount), '7CF29A', 'git')}" /></a>
  <a href="https://github.com/${username}?tab=followers"><img alt="${formattedFollowers} GitHub followers" src="${badge('FOLLOWERS', formattedFollowers, 'F5C451', 'githubsponsors')}" /></a>
</p>
<!-- PROFILE_STATS:END -->`;

const current = await readFile(readmePath, 'utf8');
const next = current.replace(
  /<!-- PROFILE_STATS:START -->[\s\S]*?<!-- PROFILE_STATS:END -->/,
  telemetry,
);

if (next === current) {
  console.log(`Profile telemetry is current: ${formattedStars} stars across ${projectCount} projects.`);
  process.exit(0);
}

if (checkOnly) {
  throw new Error(
    `Profile telemetry is stale. Expected ${formattedStars} stars across ${projectCount} projects.`,
  );
}

await writeFile(readmePath, next);
console.log(`Updated profile telemetry: ${formattedStars} stars across ${projectCount} projects.`);
