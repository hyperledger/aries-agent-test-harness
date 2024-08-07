# Aries Framework JavaScript Interoperability

## Runsets with AFJ

| Runset | ACME<br>(Issuer) | Bob<br>(Holder) | Faber<br>(Verifier) | Mallory<br>(Holder) | Scope | Results | 
| ------ | :--------------: | :-------------: | :----------------: | :-----------------: | ----- | :-----: | 
| [acapy-afj](#runset-acapy-afj) | acapy-main<br>1.0.0rc6 | javascript<br>0.5.0-alpha.97 | acapy-main<br>1.0.0rc6 | acapy-main<br>1.0.0rc6 | AIP 1.0 | [**29 / 39<br>74%**](https://allure.vonx.io/api/allure-docker-service/projects/acapy-b-javascript/reports/latest/index.html?redirect=false#behaviors) |
| [afj-acapy](#runset-afj-acapy) | javascript<br>0.5.0-alpha.97 | acapy-main<br>1.0.0rc6 | javascript<br>0.5.0-alpha.97 | javascript<br>0.5.0-alpha.97 | AIP 1.0 | [**11 / 28<br>39%**](https://allure.vonx.io/api/allure-docker-service/projects/javascript-b-acapy/reports/latest/index.html?redirect=false#behaviors) |
| [afj](#runset-afj) | javascript<br>0.5.0-alpha.97 | javascript<br>0.5.0-alpha.97 | javascript<br>0.5.0-alpha.97 | javascript<br>0.5.0-alpha.97 | AIP 1.0 | [**12 / 28<br>42%**](https://allure.vonx.io/api/allure-docker-service/projects/javascript/reports/latest/index.html?redirect=false#behaviors) |
| [javascript-ariesvcx](#runset-javascript-ariesvcx) | javascript<br>0.5.0-alpha.97 | aries-vcx<br>1.0.0 | javascript<br>0.5.0-alpha.97 | javascript<br>0.5.0-alpha.97 | AIP 1.0 | [**3 / 18<br>16%**](https://allure.vonx.io/api/allure-docker-service/projects/javascript-b-aries-vcx/reports/latest/index.html?redirect=false#behaviors) |

## Runset Notes

### Runset **acapy-afj**

Runset Name: ACA-PY to AFJ

```tip
**Latest results: 29 out of 39 (74%)**


*Last run: Wed Aug  7 00:40:39 UTC 2024*
```

#### Current Runset Status

Most of the tests are running. The tests not passing are being investigated.

*Status Note Updated: 2021.03.18*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/acapy-b-javascript/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/acapy-b-javascript/reports/latest)


### Runset **afj-acapy**

Runset Name: AFJ to ACA-PY

```tip
**Latest results: 11 out of 28 (39%)**


*Last run: Wed Aug  7 02:42:43 UTC 2024*
```

#### Current Runset Status

All AIP10 tests are currently running.

*Status Note Updated: 2021.03.17*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/javascript-b-acapy/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/javascript-b-acapy/reports/latest)


### Runset **afj**

Runset Name: AFJ to AFJ

```tip
**Latest results: 12 out of 28 (42%)**


*Last run: Wed Aug  7 02:58:13 UTC 2024*
```

#### Current Runset Status

All of the tests being executed in this runset are passing.

*Status Note Updated: 2021.03.05*

#### Runset Details

- [Results by executed Aries RFCs](https://allure.vonx.io/api/allure-docker-service/projects/javascript/reports/latest/index.html?redirect=false#behaviors)
- [Test execution history](https://allure.vonx.io/allure-docker-service-ui/projects/javascript/reports/latest)


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

