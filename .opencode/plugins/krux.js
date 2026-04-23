/**
 * Krux plugin entry point
 * Registers ork agents from the agents/ directory
 */

import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const kruxRoot = path.resolve(__dirname, '../../');
const agentsDir = path.join(kruxRoot, 'agents');

export const KruxPlugin = async ({ client, directory }) => {
  return {
    // Register agents directory so Claude Code discovers ork agents
    config: async (config) => {
      config.agents = config.agents || {};
      config.agents.paths = config.agents.paths || [];

      if (!config.agents.paths.includes(agentsDir)) {
        config.agents.paths.push(agentsDir);
      }

      // Also register skills directory for krux skills
      const skillsDir = path.join(kruxRoot, 'skills');
      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];

      if (!config.skills.paths.includes(skillsDir)) {
        config.skills.paths.push(skillsDir);
      }
    }
  };
};
