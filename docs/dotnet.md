# Aries Framework .NET Interoperability

## Runsets with AF-.NET

| Runset | ACME<br>(Issuer) | Bob<br>(Holder) | Faber<br>(Verifier) | Mallory<br>(Holder) | Scope | Results | 
| ------ | :--------------: | :-------------: | :----------------: | :-----------------: | ----- | :-----: | 
| [acapy-dotnet-javascript](#runset-acapy-dotnet-javascript) | acapy-main<br>0.8.0 | javascript<br>0.4.0-alpha.85 | dotnet<br> | acapy-main<br>0.8.0 | AIP 1.0 | [**6 / 12<br>50%**](https://allure.vonx.io/api/allure-docker-service/projects/acapy-b-javascript-f-dotnet/reports/latest/index.html?redirect=false#behaviors) |
| [acapy-dotnet](#runset-acapy-dotnet) | acapy-main<br>0.8.0 | dotnet<br> | acapy-main<br>0.8.0 | acapy-main<br>0.8.0 | AIP 1.0 | [**12 / 12<br>100%**](https://allure.vonx.io/api/allure-docker-service/projects/acapy-b-dotnet/reports/latest/index.html?redirect=false#behaviors) |
| [afj-dotnet](#runset-afj-dotnet) | javascript<br>0.4.0-alpha.85 | dotnet<br> | javascript<br>0.4.0-alpha.85 | javascript<br>0.4.0-alpha.85 | AIP 1.0 | [**2 / 12<br>16%**](https://allure.vonx.io/api/allure-docker-service/projects/javascript-b-dotnet/reports/latest/index.html?redirect=false#behaviors) |
| [dotnet-acapy](#runset-dotnet-acapy) | dotnet<br> | acapy-main<br>0.8.0 | dotnet<br> | dotnet<br> | AIP 1.0 | [**12 / 12<br>100%**](https://allure.vonx.io/api/allure-docker-service/projects/dotnet-b-acapy/reports/latest/index.html?redirect=false#behaviors) |
| [dotnet-findy](#runset-dotnet-findy) | dotnet<br> | findy<br>0.30.58 | dotnet<br> | dotnet<br> | AIP 1.0 | [**0 / 10<br>0%**](https://allure.vonx.io/api/allure-docker-service/projects/dotnet-b-findy/reports/latest/index.html?redirect=false#behaviors) |
| [dotnet-javascript](#runset-dotnet-javascript) | dotnet<br> | javascript<br>0.4.0-alpha.85 | dotnet<br> | dotnet<br> | AIP 1.0 | [**0 / 12<br>0%**](https://allure.vonx.io/api/allure-docker-service/projects/dotnet-b-javascript/reports/latest/index.html?redirect=false#behaviors) |
| [dotnet](#runset-dotnet) | dotnet<br> | dotnet<br> | dotnet<br> | dotnet<br> | AIP 1.0 | [**11 / 12<br>91%**](https://allure.vonx.io/api/allure-docker-service/projects/dotnet/reports/latest/index.html?redirect=false#behaviors) |
| [findy-dotnet](#runset-findy-dotnet) | findy<br>0.30.58 | dotnet<br> | findy<br>0.30.58 | findy<br>0.30.58 | AIP 1.0 | [**12 / 12<br>100%**](https://allure.vonx.io/api/allure-docker-service/projects/findy-b-dotnet/reports/latest/index.html?redirect=false#behaviors) |
| [findy-javascript-dotnet](#runset-findy-javascript-dotnet) | findy<br>0.30.58 | javascript<br>0.4.0-alpha.85 | dotnet<br> | findy<br>0.30.58 | AIP 1.0 | [**6 / 17<br>35%**](https://allure.vonx.io/api/allure-docker-service/projects/findy-b-javascript-f-dotnet/reports/latest/index.html?redirect=false#behaviors) |

## Runset Notes

### Runset **acapy-dotnet-javascript**

Runset Name: ACA-PY to AF-.NET to AFJ

```tip
**Latest results: 6 out of 12 (50%)**


*Last run: Mon Mar 27 01:01:47 UTC 2023*
```

#### Current Runset Status

All tests are working, except for three tests that include Faber in the test run as an issuer.
These tests are; T001-RFC0037@1.2, T001.2-RFC0037@1.2, T001.4-RFC0037@1.1 . Further investigation 
is required to determine the issue in these three tests.

*Status Note Updated: 2021.03.18*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/acapy-b-javascript-f-dotnet/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/acapy-b-javascript-f-dotnet/reports/latest)


### Runset **acapy-dotnet**

Runset Name: ACA-PY to AF-.NET

```tip
**Latest results: 12 out of 12 (100%)**


*Last run: Mon Mar 27 01:11:48 UTC 2023*
```

#### Current Runset Status

The majority of tests are running and passing. T013-HIPE0011 is failing due to the Aries Framework Dotnet not supporting
presentations containing a non-revocation interval, with a non-revocable credential. This issue is being tracked in 
https://github.com/hyperledger/aries-framework-dotnet/issues/184

*Status Note Updated: 2021.04.08*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/acapy-b-dotnet/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/acapy-b-dotnet/reports/latest)


### Runset **afj-dotnet**

Runset Name: AFJ to AF-.NET

```tip
**Latest results: 2 out of 12 (16%)**


*Last run: Mon Mar 27 01:48:35 UTC 2023*
```

#### Current Runset Status

All of the tests being executed in this runset are passing.

*Status Note Updated: 2021.03.05*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/javascript-b-dotnet/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/javascript-b-dotnet/reports/latest)


### Runset **dotnet-acapy**

Runset Name: AF-.NET to ACA-PY

```tip
**Latest results: 12 out of 12 (100%)**


*Last run: Mon Mar 27 02:29:59 UTC 2023*
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
**Latest results: 0 out of 10 (0%)**


*Last run: Mon Mar 27 02:36:02 UTC 2023*
```

#### Current Runset Status

Two connection tests are passing out of Nineteen total. There are multiple issues in Issue Credential and Proof
with dotnet as the issuer and findy as the holder. Removed a large portion of Proof tests since jobs were getting cancelled.
These will be added back when tests or agents are fixed and stability has returned.

*Status Note Updated: 2022.01.28*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/dotnet-b-findy/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/dotnet-b-findy/reports/latest)


### Runset **dotnet-javascript**

Runset Name: AF-.NET to AFJ

```tip
**Latest results: 0 out of 12 (0%)**


*Last run: Mon Mar 27 02:46:48 UTC 2023*
```

#### Current Runset Status

More tests are failing than are passing when Aries Framework .NET is playing the issuer role. More investigation is needed.

*Status Note Updated: 2021.03.18*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/dotnet-b-javascript/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/dotnet-b-javascript/reports/latest)


### Runset **dotnet**

Runset Name: AF-.NET to AF-.NET

```tip
**Latest results: 11 out of 12 (91%)**


*Last run: Mon Mar 27 02:57:29 UTC 2023*
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
**Latest results: 12 out of 12 (100%)**


*Last run: Mon Mar 27 02:56:48 UTC 2023*
```

#### Current Runset Status

All test scenarios are passing. 

*Status Note Updated: 2021.10.15*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/findy-b-dotnet/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/findy-b-dotnet/reports/latest)


### Runset **findy-javascript-dotnet**

Runset Name: findy to AFJ to AF-.NET

```tip
**Latest results: 6 out of 17 (35%)**


*Last run: Mon Mar 27 03:00:43 UTC 2023*
```

#### Current Runset Status

All of the tests being executed in this runset are passing. 

*Status Note Updated: 2021.10.15*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/findy-b-javascript-f-dotnet/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/findy-b-javascript-f-dotnet/reports/latest)

Jump back to the [interoperability summary](./README.md).

