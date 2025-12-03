const resolvedOptions = {
  enabled: true,
  clean: true,
  reportsDirectory: 'coverage',
  reporter: ['text', 'json', 'html'],
  exclude: ['node_modules/', 'src/__tests__/'],
  provider: 'v8',
}

const noop = () => {}

const provider = {
  name: 'local-v8-stub',
  options: resolvedOptions,
  initialize: noop,
  resolveOptions: () => resolvedOptions,
  clean: noop,
  onAfterSuiteRun: noop,
  onFileTransform: () => null,
  reportCoverage: async () => {},
}

export default {
  getProvider() {
    return provider
  },
  startCoverage: async () => null,
  takeCoverage: async () => null,
  stopCoverage: async () => null,
}
