
using System;
using DotNet.Backchannel.Handlers;
using Hyperledger.Aries.Agents;

namespace DotNet.Backchannel
{
    public class TestAgent : AgentBase
    {
        public TestAgent(IServiceProvider serviceProvider)
            : base(serviceProvider)
        {
        }

        protected override void ConfigureHandlers()
        {
            AddConnectionHandler();
            AddTrustPingHandler();
            AddBasicMessageHandler();
            AddProofHandler();
            AddCredentialHandler();
            AddForwardHandler();
            // Framework doesn't send ack after verifying presentation
            AddHandler<PresentationAckHandler>();
        }
    }
}