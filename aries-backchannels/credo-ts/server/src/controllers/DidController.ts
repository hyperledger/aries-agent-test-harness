import { Controller, Get } from '@tsed/common'
import { BaseController } from '../BaseController'
import { TestHarnessConfig } from '../TestHarnessConfig'

@Controller('/agent/command/did')
export class DidController extends BaseController {
  public constructor(testHarnessConfig: TestHarnessConfig) {
    super(testHarnessConfig)
  }

  @Get()
  async getPublicDid() {
    const publicDidInfoRecord = await this.agent.genericRecords.findById('PUBLIC_DID_INFO')
    return publicDidInfoRecord ? publicDidInfoRecord.content.didInfo : {}
  }
}
