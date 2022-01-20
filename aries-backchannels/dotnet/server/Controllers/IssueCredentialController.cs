using System;
using Microsoft.AspNetCore.Mvc;
using System.Threading.Tasks;
using DotNet.Backchannel.Models;
using Microsoft.Extensions.Caching.Memory;
using DotNet.Backchannel.Messages;

using Hyperledger.Aries.Features.IssueCredential;
using Hyperledger.Aries.Storage;
using Hyperledger.Aries.Agents;
using Hyperledger.Aries.Utils;
using Hyperledger.Aries.Features.DidExchange;
using Hyperledger.Aries.Models.Events;
using Hyperledger.Aries.Contracts;

using System.Reactive.Linq;
using Hyperledger.Aries.Configuration;
using Hyperledger.Indy.AnonCredsApi;
using Newtonsoft.Json.Linq;
using System.Linq;
using Hyperledger.Aries.Decorators.Attachments;
using Hyperledger.Aries.Extensions;
using Hyperledger.Aries.Decorators.Threading;

namespace DotNet.Backchannel.Controllers
{
    [Route("agent/command/issue-credential")]
    [ApiController]
    public class IssueCredentialController : ControllerBase
    {
        private readonly ICredentialService _credentialService;
        private readonly IWalletRecordService _recordService;
        private readonly IEventAggregator _eventAggregator;
        private readonly IProvisioningService _provisionService;
        private readonly IConnectionService _connectionService;
        private readonly IAgentProvider _agentContextProvider;
        private readonly IMessageService _messageService;
        private IMemoryCache _credentialCache;

        public IssueCredentialController(
            ICredentialService credentialService,
            IWalletRecordService recordService,
            IEventAggregator eventAggregator,
            IProvisioningService provisionService,
            IConnectionService connectionService,
            IAgentProvider agentContextProvider,
            IMessageService messageService,
            IMemoryCache memoryCache
            )
        {
            _credentialService = credentialService;
            _recordService = recordService;
            _eventAggregator = eventAggregator;
            _provisionService = provisionService;
            _connectionService = connectionService;
            _agentContextProvider = agentContextProvider;
            _messageService = messageService;
            _credentialCache = memoryCache;
        }

        [HttpGet("{threadId}")]
        public async Task<IActionResult> GetCredentialRecordByThreadIdAsync([FromRoute] string threadId)
        {
            var context = await _agentContextProvider.GetContextAsync();

            try
            {
                var credentialRecord = await _credentialService.GetByThreadIdAsync(context, threadId);
                var THCredentialExchange = _credentialCache.Get<TestHarnessCredentialExchange>(threadId);
                if (THCredentialExchange == null) return NotFound();

                return Ok(THCredentialExchange);
            }
            catch
            {
                // Can't find the credential record
                return NotFound();
            }
        }

        [HttpPost("send-proposal")]
        public Task<IActionResult> SendCredentialProposalAsync(OperationBody body)
        {
            throw new NotImplementedException("Send proposal not supported for .NET backchannel");
        }

        [HttpPost("send-offer")]
        public async Task<IActionResult> SendCredentialOfferAsync(OperationBody body)
        {
            var context = await _agentContextProvider.GetContextAsync();
            var issuer = await _provisionService.GetProvisioningAsync(context.Wallet);
            var threadId = body.Id;

            string connectionId;
            TestHarnessCredentialExchange THCredentialExchange;
            CredentialOfferMessage credentialOffer;
            CredentialRecord credentialRecord;

            // Adding a delay here. It seems that with the removal of the state checks in the tests,
            // Some agents are not yet in the appropriate state for this call. 
            // TODO There may be a better way to do this but adding the wait is a quick fix to get the tests
            // running again.
            await Task.Delay(5000);

            // Send offer in response to proposal
            if (threadId != null)
            {
                throw new NotSupportedException("Credential proposal not supported in .NET backchannel");
            }
            // Send Offer to start credential issuance flow
            else
            {
                var offer = body.Data;
                connectionId = (string)offer["connection_id"];
                var credentialPreview = offer["credential_preview"].ToObject<CustomCredentialPreviewMessage>();
                var credentialDefinitionId = (string)offer["cred_def_id"];

                credentialPreview.Attributes = CleanCredentialPreviewAttributes(credentialPreview.Attributes);

                (credentialOffer, credentialRecord) = await _credentialService.CreateOfferAsync(context, new OfferConfiguration
                {
                    CredentialAttributeValues = credentialPreview.Attributes,
                    CredentialDefinitionId = credentialDefinitionId,
                    IssuerDid = issuer.IssuerDid
                }, connectionId);

                THCredentialExchange = new TestHarnessCredentialExchange
                {
                    RecordId = credentialRecord.Id,
                    ThreadId = credentialRecord.GetTag(TagConstants.LastThreadId),
                    State = TestHarnessCredentialExchangeState.OfferSent
                };
                _credentialCache.Set(THCredentialExchange.ThreadId, THCredentialExchange);
            }

            var connection = await _connectionService.GetAsync(context, connectionId);

            // Listen for credential request to update the state
            UpdateStateOnMessage(THCredentialExchange, TestHarnessCredentialExchangeState.RequestReceived, _ => new[] { MessageTypes.IssueCredentialNames.RequestCredential, MessageTypesHttps.IssueCredentialNames.RequestCredential, }.Contains(_.MessageType) && _.ThreadId == THCredentialExchange.ThreadId);

            await _messageService.SendAsync(context, credentialOffer, connection);

            return Ok(THCredentialExchange);
        }

        [HttpPost("send-request")]
        public async Task<IActionResult> SendCredentialRequestAsync(OperationBody body)
        {
            // Indy does not support startign from a credential-request. So the id is always the thread id
            var threadId = body.Id;
            var THCredentialExchange = _credentialCache.Get<TestHarnessCredentialExchange>(threadId);
            var context = await _agentContextProvider.GetContextAsync();

            var (credentialRequest, credentialRecord) = await _credentialService.CreateRequestAsync(context, THCredentialExchange.RecordId);
            THCredentialExchange.State = TestHarnessCredentialExchangeState.RequestSent;

            // Listen for issue credential to update the state
            UpdateStateOnMessage(THCredentialExchange, TestHarnessCredentialExchangeState.CredentialReceived, _ => new[] { MessageTypes.IssueCredentialNames.IssueCredential, MessageTypesHttps.IssueCredentialNames.IssueCredential }.Contains(_.MessageType) && _.ThreadId == THCredentialExchange.ThreadId);

            var connection = await _connectionService.GetAsync(context, credentialRecord.ConnectionId);
            await _messageService.SendAsync(context, credentialRequest, connection);

            return Ok(THCredentialExchange);
        }

        [HttpPost("issue")]
        public async Task<IActionResult> IssueCredentialAsync(OperationBody body)
        {

            // Adding a delay here. It seems that with the removal of the state checks in the tests,
            // Some agents are not yet in the appropriate state for this call. 
            // TODO There may be a better way to do this but adding the wait is a quick fix to get the tests
            // running again.
            await Task.Delay(10000);

            var threadId = body.Id;
            var context = await _agentContextProvider.GetContextAsync();
            var THCredentialExchange = _credentialCache.Get<TestHarnessCredentialExchange>(threadId);

            // NOTE: We currently don't use the body from issue credential, but the data from the credential
            // I think this must be the same, otherwise a new offer must be sent before issuing other data
            var (credentialIssueMessage, credentialRecord) = await _credentialService.CreateCredentialAsync(context, THCredentialExchange.RecordId);
            var connection = await _connectionService.GetAsync(context, credentialRecord.ConnectionId);

            await _messageService.SendAsync(context, credentialIssueMessage, connection);

            THCredentialExchange.State = TestHarnessCredentialExchangeState.CredentialIssued;

            return Ok(THCredentialExchange);
        }

        [HttpPost("store")]
        public async Task<IActionResult> StoreCredentialAsync(OperationBody body)
        {
            var threadId = body.Id;
            var context = await _agentContextProvider.GetContextAsync();
            var THCredentialExchange = _credentialCache.Get<TestHarnessCredentialExchange>(threadId);
            var credentialRecord = await _credentialService.GetAsync(context, THCredentialExchange.RecordId);

            THCredentialExchange.CredentialId = credentialRecord.CredentialId;
            THCredentialExchange.State = TestHarnessCredentialExchangeState.Done;

            return Ok(THCredentialExchange);
        }

        /// <summary>
        /// prevent mime type not supported error when mime type is null
        /// </summary>
        /// <param name="attributes"></param>
        /// <returns></returns>
        private CredentialPreviewAttribute[] CleanCredentialPreviewAttributes(CredentialPreviewAttribute[] attributes) => attributes.Select(x =>
            new CredentialPreviewAttribute
            {
                Name = x.Name,
                MimeType = x.MimeType == null ? CredentialMimeTypes.TextMimeType : x.MimeType,
                Value = x.Value?.ToString()
            }).ToArray();

        private void UpdateStateOnMessage(TestHarnessCredentialExchange testHarnessCredentialExchange, TestHarnessCredentialExchangeState nextState, Func<ServiceMessageProcessingEvent, bool> predicate)
        {
            _eventAggregator.GetEventByType<ServiceMessageProcessingEvent>()
            .Where(predicate)
            .Take(1)
            .Subscribe(_ => { testHarnessCredentialExchange.State = nextState; });
        }
    }
}
