using System;
using Microsoft.AspNetCore.Mvc;
using System.Threading.Tasks;
using DotNet.Backchannel.Models;
using Hyperledger.Aries.Features.PresentProof;
using Hyperledger.Aries.Storage;
using Hyperledger.Aries.Contracts;
using Hyperledger.Aries.Configuration;
using Hyperledger.Aries.Features.DidExchange;
using Hyperledger.Aries.Agents;
using Microsoft.Extensions.Caching.Memory;
using Hyperledger.Aries.Utils;
using Hyperledger.Aries.Models.Events;
using System.Reactive.Linq;
using System.Linq;
using Microsoft.Extensions.Logging;
using System.Collections.Generic;
using Hyperledger.Indy.AnonCredsApi;
using DotNet.Backchannel.Messages;
using Hyperledger.Aries.Extensions;
using Hyperledger.Aries.Decorators.Threading;

namespace DotNet.Backchannel.Controllers
{
    [Route("agent/command/proof")]
    [ApiController]
    public class PresentProofController : ControllerBase
    {
        private readonly IProofService _proofService;
        private readonly IWalletRecordService _recordService;
        private readonly IEventAggregator _eventAggregator;
        private readonly IProvisioningService _provisionService;
        private readonly IConnectionService _connectionService;
        private readonly IAgentProvider _agentContextProvider;
        private readonly IMessageService _messageService;
        private IMemoryCache _proofCache;

        private ILogger<PresentProofController> _logger;

        public PresentProofController(

             IProofService proofService,
            IWalletRecordService recordService,
            IEventAggregator eventAggregator,
            IProvisioningService provisionService,
            IConnectionService connectionService,
            IAgentProvider agentContextProvider,
            IMessageService messageService,
            IMemoryCache memoryCache,
            ILogger<PresentProofController> logger

            )
        {
            _proofService = proofService;
            _recordService = recordService;
            _eventAggregator = eventAggregator;
            _provisionService = provisionService;
            _connectionService = connectionService;
            _agentContextProvider = agentContextProvider;
            _messageService = messageService;
            _proofCache = memoryCache;
            _logger = logger;
        }

        [HttpGet("{threadId}")]
        public async Task<IActionResult> GetProofRecordByThreadIdAsync([FromRoute] string threadId)
        {
            var context = await _agentContextProvider.GetContextAsync();

            try
            {
                var proofRecord = await _proofService.GetByThreadIdAsync(context, threadId);
                var THProofExchange = _proofCache.Get<TestHarnessPresentationExchange>(threadId);
                if (THProofExchange == null) return NotFound();

                return Ok(THProofExchange);
            }
            catch
            {
                // Can't find the proof record
                return NotFound();
            }
        }

        [HttpPost("send-proposal")]
        public Task<IActionResult> SendPresentationProposalAsync(OperationBody body)
        {
            throw new NotImplementedException("Send proposal not supported for .NET backchannel");
        }

        [HttpPost("send-request")]
        public async Task<IActionResult> SendPresentationRequestAsync(OperationBody body)
        {
            // NOTE: AATH can only start from presentation request, not respond to previous message
            var context = await _agentContextProvider.GetContextAsync();

            var presentationRequest = body.Data;
            var connectionId = (string)presentationRequest["connection_id"];
            var presentationRequestMessage = presentationRequest["presentation_request"]["proof_request"]["data"];

            var proofRequest = new ProofRequest
            {
                Name = (string)presentationRequestMessage["name"] ?? "test proof",
                Version = (string)presentationRequestMessage["version"] ?? "1.0",
                Nonce = await AnonCreds.GenerateNonceAsync(),
                RequestedAttributes = presentationRequestMessage["requested_attributes"]?.ToObject<Dictionary<string, ProofAttributeInfo>>() ?? new Dictionary<string, ProofAttributeInfo> { },
                RequestedPredicates = presentationRequestMessage["requested_predicates"]?.ToObject<Dictionary<string, ProofPredicateInfo>>() ?? new Dictionary<string, ProofPredicateInfo> { }
            };

            _logger.LogInformation("SendPresentationRequest {proofRequest}", proofRequest.ToJson());


            var (requestPresentationMessage, proofRecord) = await _proofService.CreateRequestAsync(context, proofRequest, connectionId);

            var connection = await _connectionService.GetAsync(context, connectionId);

            var THPresentationExchange = new TestHarnessPresentationExchange
            {
                RecordId = proofRecord.Id,
                ThreadId = proofRecord.GetTag(TagConstants.LastThreadId),
                State = TestHarnessPresentationExchangeState.RequestSent
            };
            _proofCache.Set(THPresentationExchange.ThreadId, THPresentationExchange);

            UpdateStateOnMessage(THPresentationExchange, TestHarnessPresentationExchangeState.PresentationReceived, _ => new[] { MessageTypes.PresentProofNames.Presentation, MessageTypesHttps.PresentProofNames.Presentation }.Contains(_.MessageType) && _.ThreadId == THPresentationExchange.ThreadId);

            _logger.LogDebug("Send Presentation Request {requestPresentationMessage}", requestPresentationMessage.ToJson());

            await _messageService.SendAsync(context, requestPresentationMessage, connection);

            return Ok(THPresentationExchange);
        }

        [HttpPost("send-presentation")]
        public async Task<IActionResult> SendProofPresentationAsync(OperationBody body)
        {
            var context = await _agentContextProvider.GetContextAsync();

            var threadId = body.Id;
            var THPresentationExchange = _proofCache.Get<TestHarnessPresentationExchange>(threadId);
            var requestedCredentialsJson = body.Data;

            var requestedCredentials = requestedCredentialsJson.ToObject<RequestedCredentials>();

            _logger.LogInformation("SendProofPresentation {id} {requestedCredentials}", THPresentationExchange.RecordId, requestedCredentials.ToJson());

            var (presentationMessage, proofRecord) = await _proofService.CreatePresentationAsync(context, THPresentationExchange.RecordId, requestedCredentials);

            var connection = await _connectionService.GetAsync(context, proofRecord.ConnectionId);

            THPresentationExchange.State = TestHarnessPresentationExchangeState.PresentationSent;

            _logger.LogDebug("Send Presentation {presentationMessage}", presentationMessage.ToJson());

            await _messageService.SendAsync(context, presentationMessage, connection);

            return Ok(THPresentationExchange);
        }

        [HttpPost("verify-presentation")]
        public async Task<IActionResult> VerifyPresentation(OperationBody body)
        {
            // Adding a delay here. It seems that with the removal of the state checks in the tests,
            // Some agents are not yet in the appropriate state for this call. 
            // TODO There may be a better way to do this but adding the wait is a quick fix to get the tests
            // running again.
            await Task.Delay(10000);

            var context = await _agentContextProvider.GetContextAsync();
            var threadId = body.Id;
            var THPresentationExchange = _proofCache.Get<TestHarnessPresentationExchange>(threadId);
            var proofRecord = await _proofService.GetByThreadIdAsync(context, THPresentationExchange.ThreadId);
            var connectionRecord = await _connectionService.GetAsync(context, proofRecord.ConnectionId);

            _logger.LogInformation("VerifyPresentation {proofRecord}", proofRecord.ToJson());

            var isValid = await _proofService.VerifyProofAsync(context, THPresentationExchange.RecordId);

            if (!isValid)
            {
                return Problem("Proof is not valid");
            }

            THPresentationExchange.State = TestHarnessPresentationExchangeState.Done;
            var ackPresentationMessage = new AckPresentationMessage()
            {
                Status = "OK"
            };

            ackPresentationMessage.ThreadFrom(threadId);

            await _messageService.SendAsync(context, ackPresentationMessage, connectionRecord);

            return Ok(THPresentationExchange);
        }

        private void UpdateStateOnMessage(TestHarnessPresentationExchange THPresentationExchange, TestHarnessPresentationExchangeState nextState, Func<ServiceMessageProcessingEvent, bool> predicate)
        {
            _eventAggregator.GetEventByType<ServiceMessageProcessingEvent>()
            .Where(predicate)
            .Take(1)
            .Subscribe(_ => { THPresentationExchange.State = nextState; });
        }
    }
}
