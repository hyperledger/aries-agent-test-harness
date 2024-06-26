import { Controller, Get, PathParams } from '@tsed/common'
import { CredentialUtils } from '../utils/CredentialUtils'
import { BaseController } from '../BaseController'
import { TestHarnessConfig } from '../TestHarnessConfig'

@Controller('/agent/command/credential')
export class CredentialController extends BaseController {
  public constructor(testHarnessConfig: TestHarnessConfig) {
    super(testHarnessConfig)
  }

  @Get('/:credentialId')
  async getCredentialById(@PathParams('credentialId') credentialId: string) {
    return await CredentialUtils.getAnonCredsCredentialById(this.agent, credentialId)
  }
}
