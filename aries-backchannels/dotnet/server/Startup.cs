using System;
using DotNet.Backchannel.Handlers;
using DotNet.Backchannel.Middlewares;
using Hyperledger.Aries.Agents;
using Hyperledger.Aries.Storage;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Newtonsoft.Json.Converters;

namespace DotNet.Backchannel
{
    public class Startup
    {
        public Startup(IConfiguration configuration)
        {
            Configuration = configuration;
        }

        public IConfiguration Configuration { get; }

        // This method gets called by the runtime. Use this method to add services to the container.
        public void ConfigureServices(IServiceCollection services)
        {
            services.AddControllers()
            // Aries Framework .NET uses Newtonsoft JSON library
            .AddNewtonsoftJson(options =>
            {
                // Convert Enum values to string values
                options.SerializerSettings.Converters.Add(new StringEnumConverter());
            });

            services.AddLogging();

            // Add in memory cache to store invitations
            services.AddMemoryCache();



            services.AddAriesFramework(builder =>
            {
                builder.Services.AddSingleton<IAgentMiddleware, MessageAgentMiddleware>();
                builder.Services.AddSingleton<PresentationAckHandler>();

                builder.RegisterAgent<DotNet.Backchannel.TestAgent>(c =>
                {
                    c.AgentName = "dotnet." + (Environment.GetEnvironmentVariable("AGENT_NAME") ?? "Agent");
                    c.EndpointUri = Environment.GetEnvironmentVariable("ENDPOINT_HOST");
                    c.WalletConfiguration = new WalletConfiguration { Id = "TestAgentWallet" };
                    c.WalletCredentials = new WalletCredentials { Key = "MyWalletKey" };
                    c.GenesisFilename = Environment.GetEnvironmentVariable("GENESIS_PATH");
                    c.IssuerKeySeed = Environment.GetEnvironmentVariable("ISSUER_KEY_SEED");
                });
            });
        }

        // This method gets called by the runtime. Use this method to configure the HTTP request pipeline.
        public void Configure(IApplicationBuilder app, IWebHostEnvironment env)
        {
            if (env.IsDevelopment())
            {
                app.UseDeveloperExceptionPage();
            }

            // Register agent middleware
            app.UseAriesFramework();

            app.UseRouting();

            app.UseEndpoints(endpoints =>
            {
                endpoints.MapControllers();
            });
        }
    }
}
