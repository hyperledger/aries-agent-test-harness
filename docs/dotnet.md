# Aries Framework .NET Interoperability

## Runsets with AF-.NET

| Runset | ACME<br>(Issuer) | Bob<br>(Holder) | Faber<br>(Verifier) | Mallory<br>(Holder) | Scope | Results | 
| ------ | :--------------: | :-------------: | :----------------: | :-----------------: | ----- | :-----: | 
| [acapy-dotnet](#runset-acapy-dotnet) | acapy-main<br>0.12.0rc2 | dotnet<br> | acapy-main<br>0.12.0rc2 | acapy-main<br>0.12.0rc2 | AIP 1.0 | [**0 / 0<br>0%**](https://allure.vonx.io/api/allure-docker-service/projects/acapy-b-dotnet/reports/latest/index.html?redirect=false#behaviors) |
| [dotnet-acapy](#runset-dotnet-acapy) | dotnet<br> | acapy-main<br>0.12.0rc2 | dotnet<br> | dotnet<br> | AIP 1.0 | [**0 / 0<br>0%**](https://allure.vonx.io/api/allure-docker-service/projects/dotnet-b-acapy/reports/latest/index.html?redirect=false#behaviors) |
| [dotnet-findy](#runset-dotnet-findy) | dotnet<br> | findy<br>0.31.58 | dotnet<br> | dotnet<br> | AIP 1.0 | [**0 / 0<br>0%**](https://allure.vonx.io/api/allure-docker-service/projects/dotnet-b-findy/reports/latest/index.html?redirect=false#behaviors) |
| [dotnet](#runset-dotnet) | dotnet<br> | dotnet<br> | dotnet<br> | dotnet<br> | AIP 1.0 | [**0 / 0<br>0%**](https://allure.vonx.io/api/allure-docker-service/projects/dotnet/reports/latest/index.html?redirect=false#behaviors) |
| [findy-dotnet](#runset-findy-dotnet) | findy<br>0.31.58 | dotnet<br> | findy<br>0.31.58 | findy<br>0.31.58 | AIP 1.0 | [**0 / 0<br>0%**](https://allure.vonx.io/api/allure-docker-service/projects/findy-b-dotnet/reports/latest/index.html?redirect=false#behaviors) |

## Runset Notes

### Runset **acapy-dotnet**

Runset Name: ACA-PY to AF-.NET

```tip
**Latest results: 0 out of 0 (0%)**


*Last run: Wed Mar 27 01:48:47 UTC 2024*
```

#### Current Runset Status

The majority of tests are running and passing. T013-HIPE0011 is failing due to the Aries Framework Dotnet not supporting
presentations containing a non-revocation interval, with a non-revocable credential. This issue is being tracked in 
https://github.com/hyperledger/aries-framework-dotnet/issues/184

*Status Note Updated: 2021.04.08*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/acapy-b-dotnet/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/acapy-b-dotnet/reports/latest)


### Runset **dotnet-acapy**

Runset Name: AF-.NET to ACA-PY

```tip
**Latest results: 0 out of 0 (0%)**


*Last run: Wed Mar 27 01:48:52 UTC 2024*
```

#### Current Runset Status

More tests are failing than are passing when Aries Framework .NET is playing the issuer role. More investigation is needed.

*Status Note Updated: 2021.03.17*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/dotnet-b-acapy/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/dotnet-b-acapy/reports/latest)


### Runset **dotnet-findy**

Runset Name: dotnet to findy

```tip
**Latest results: 0 out of 0 (0%)**


*Last run: Wed Mar 27 01:48:52 UTC 2024*
```

#### Current Runset Status

Two connection tests are passing out of Nineteen total. There are multiple issues in Issue Credential and Proof
with dotnet as the issuer and findy as the holder. Removed a large portion of Proof tests since jobs were getting cancelled.
These will be added back when tests or agents are fixed and stability has returned.

*Status Note Updated: 2022.01.28*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/dotnet-b-findy/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/dotnet-b-findy/reports/latest)


### Runset **dotnet**

Runset Name: AF-.NET to AF-.NET

```tip
**Latest results: 0 out of 0 (0%)**


*Last run: Wed Mar 27 01:48:53 UTC 2024*
```

#### Current Runset Status

All of the tests being executed in this runset are passing.

*Status Note Updated: 2021.03.05*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/dotnet/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/dotnet/reports/latest)


### Runset **findy-dotnet**

Runset Name: findy to dotnet

```tip
**Latest results: 0 out of 0 (0%)**


*Last run: Wed Mar 27 01:48:54 UTC 2024*
```

#### Current Runset Status

All test scenarios are passing. 

*Status Note Updated: 2021.10.15*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/findy-b-dotnet/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/findy-b-dotnet/reports/latest)

Jump back to the [interoperability summary](./README.md).

