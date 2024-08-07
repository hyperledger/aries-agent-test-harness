# AriesVCX Interoperability

## Runsets with VCX

| Runset | ACME<br>(Issuer) | Bob<br>(Holder) | Faber<br>(Verifier) | Mallory<br>(Holder) | Scope | Results | 
| ------ | :--------------: | :-------------: | :----------------: | :-----------------: | ----- | :-----: | 
| [acapy-ariesvcx](#runset-acapy-ariesvcx) | acapy-main<br>1.0.0rc6 | aries-vcx<br>0.65.0 | acapy-main<br>1.0.0rc6 | acapy-main<br>1.0.0rc6 | AIP 1.0 | [**0 / 28<br>0%**](https://allure.vonx.io/api/allure-docker-service/projects/acapy-b-aries-vcx/reports/latest/index.html?redirect=false#behaviors) |
| [ariesvcx-acapy](#runset-ariesvcx-acapy) | aries-vcx<br>0.65.0 | acapy-main<br>1.0.0rc6 | aries-vcx<br>0.65.0 | aries-vcx<br>0.65.0 | AIP 1.0 | [**0 / 28<br>0%**](https://allure.vonx.io/api/allure-docker-service/projects/aries-vcx-b-acapy/reports/latest/index.html?redirect=false#behaviors) |
| [ariesvcx-ariesvcx](#runset-ariesvcx-ariesvcx) | aries-vcx<br>0.65.0 | aries-vcx<br>0.65.0 | aries-vcx<br>0.65.0 | aries-vcx<br>0.65.0 | AIP 1.0 | [**0 / 32<br>0%**](https://allure.vonx.io/api/allure-docker-service/projects/aries-vcx/reports/latest/index.html?redirect=false#behaviors) |
| [javascript-ariesvcx](#runset-javascript-ariesvcx) | javascript<br>0.5.0-alpha.97 | aries-vcx<br>1.0.0 | javascript<br>0.5.0-alpha.97 | javascript<br>0.5.0-alpha.97 | AIP 1.0 | [**3 / 18<br>16%**](https://allure.vonx.io/api/allure-docker-service/projects/javascript-b-aries-vcx/reports/latest/index.html?redirect=false#behaviors) |

## Runset Notes

### Runset **acapy-ariesvcx**

Runset Name: acapy to aries-vcx

```tip
**Latest results: 0 out of 28 (0%)**


*Last run: Wed Aug  7 01:44:07 UTC 2024*
```

#### Current Runset Status

RFC0023 is disabled due to inconsistent results. RFC0793 is also being investigated: https://github.com/hyperledger/aries-vcx/issues/1252
*Status Note Updated: 2024.07.05*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/acapy-b-aries-vcx/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/acapy-b-aries-vcx/reports/latest)


### Runset **ariesvcx-acapy**

Runset Name: aries-vcx to acapy

```tip
**Latest results: 0 out of 28 (0%)**


*Last run: Wed Aug  7 03:04:32 UTC 2024*
```

#### Current Runset Status

Most tests are currently struggling, due to aries-vcx reporting the wrong connection state to the
backchannel. Being resolved here: https://github.com/hyperledger/aries-vcx/issues/1253
@RFC0793 has relatively low success due to aries-vcx not supporting full range of DID methods in
these tests.
*Status Note Updated: 2024.07.05*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/aries-vcx-b-acapy/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/aries-vcx-b-acapy/reports/latest)


### Runset **ariesvcx-ariesvcx**

Runset Name: aries-vcx to aries-vcx

```tip
**Latest results: 0 out of 32 (0%)**


*Last run: Wed Aug  7 03:08:26 UTC 2024*
```

#### Current Runset Status

@RFC0793 has some failures due to aries-vcx not supporting full range of DID methods in
these tests.
*Status Note Updated: 2024.07.05*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/aries-vcx/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/aries-vcx/reports/latest)


### Runset **javascript-ariesvcx**

Runset Name: javascript to aries-vcx

```tip
**Latest results: 3 out of 18 (16%)**


*Last run: Mon May 13 02:34:19 UTC 2024*
```

#### Current Runset Status
```warning
No test status note is available for this runset. Please update: .github/workflows/test-harness-javascript-ariesvcx.yml.
```

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/javascript-b-aries-vcx/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/javascript-b-aries-vcx/reports/latest)

Jump back to the [interoperability summary](./README.md).

