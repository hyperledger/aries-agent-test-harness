import { TestHarnessConfig } from './TestHarnessConfig'

export abstract class BaseController {
  protected testHarnessConfig: TestHarnessConfig

  public constructor(testHarnessConfig: TestHarnessConfig) {
    this.testHarnessConfig = testHarnessConfig

    this.testHarnessConfig.addController(this)
  }

  protected get agent() {
    return this.testHarnessConfig.agent
  }

  public onStartup(): Promise<void> | void {}
}
