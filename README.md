# CyberArk Conjur Kubernetes JWT Authentication

## Zero Hardcoded Credentials Using Kubernetes Pod Identity

This project demonstrates enterprise-grade secrets delivery to Kubernetes workloads using CyberArk Conjur's JWT authenticator. Kubernetes pods authenticate to Conjur using their native service account JWT tokens with zero hardcoded credentials anywhere in the container image, environment variables, or Kubernetes Secrets.

## Business Problem

Most enterprises running Kubernetes store application credentials in one of three ways:

- Hardcoded in container images (credentials baked into Docker layers)
- Kubernetes Secrets (base64 encoded, not encrypted, readable by anyone with kubectl access)
- Environment variables (visible in pod specs, logged in crash dumps)

All three approaches leave application credentials completely outside the PAM governance boundary. Security teams running CyberArk have no visibility into these credentials because they were never onboarded into the vault.

This project eliminates all three approaches by replacing static credentials with identity-based dynamic secret retrieval.

## Architecture

```
Kubernetes Pod starts
        ↓
Pod presents Kubernetes service account JWT token to Conjur
        ↓
Conjur validates JWT against Kubernetes OIDC endpoint
        ↓
Conjur checks authorization policy
        ↓
Secret delivered dynamically at runtime
        ↓
Zero static credentials anywhere
```

## What This Proves

| Capability | Status |
|---|---|
| Conjur OSS 1.24.0 with JWT authenticator | ✅ Deployed and configured |
| Kubernetes service account identity authentication | ✅ Proven end to end |
| Dynamic secret retrieval at pod runtime | ✅ DB_PASSWORD retrieved successfully |
| Authorization boundary enforcement | ✅ Unauthorized pods receive 401 denial |
| Zero hardcoded credentials in container image | ✅ Verified |
| Zero Kubernetes Secrets used | ✅ Verified |
| Compliance mapping | ✅ NIST AI RMF, OWASP LLM Top 10 LLM06, MITRE ATLAS |

## Authentication Flow

The Conjur JWT authenticator uses Kubernetes as an identity provider. When a pod authenticates:

1. Pod reads its mounted service account JWT from `/var/run/secrets/kubernetes.io/serviceaccount/token`
2. Pod sends JWT to Conjur's `/authn-jwt/k8s/dev/authenticate` endpoint
3. Conjur validates the JWT signature against Kubernetes OIDC public keys
4. Conjur verifies the `sub` claim matches the authorized host identity
5. Conjur returns a short-lived Conjur access token
6. Pod uses the access token to retrieve secrets from the Conjur vault

## Compliance Mapping

| Finding | Framework | Control |
|---|---|---|
| Hardcoded credentials eliminated | LLM06 Excessive Agency | Requirement 8.6.1 |
| Dynamic credential delivery | IA-5 Authenticator Management | Requirement 8.2.2 |
| Audit trail for every retrieval | AU-2 Event Logging | Requirement 10.2.1 |
| Authorization boundary enforcement | AC-3 Access Enforcement | Requirement 7.2.1 |

## Environment

- Conjur OSS 1.24.0 running in Docker
- Nginx SSL proxy on ports 8080/8443
- Minikube v1.38.1 on Docker Desktop
- kubectl v1.36.2
- authn-jwt/k8s authenticator

## Repository Structure

```
├── docker-compose.yml          # Conjur OSS + Nginx SSL proxy
├── nginx.conf                  # SSL proxy configuration
├── clean-policy.yml            # Conjur JWT authenticator policy
├── conjur-clusterrole.yml      # Kubernetes RBAC for Conjur
├── jwt-demo-app.yml            # Authorized pod manifest
├── unauth-demo.yml             # Unauthorized pod (401 proof)
├── app/
│   ├── Dockerfile              # Alpine with curl
│   └── app.py                  # Demo application
└── LICENSE
```

> Note: Configuration files (docker-compose.yml, nginx.conf, policy YAMLs)
> contain environment-specific values (Conjur account IDs, cluster endpoints,
> namespace names) and are maintained outside the public repository.
> The README documents the architecture, authentication flow, and proven
> results. Contact curtis@igasecurityconsulting.com for implementation details.

## Demo Results

### Authorized Pod Output
```
=== Conjur Kubernetes JWT Authentication Demo ===
Pod: jwt-demo | Namespace: demo-app | Service Account: conjur-demo

Step 1: Authenticating to Conjur using Kubernetes JWT identity...
SUCCESS: JWT authentication completed
Conjur access token received (length: 708 chars)

Step 2: Retrieving secret from Conjur vault...

=== RESULT ===
DB_PASSWORD=[secret value retrieved successfully]

Zero hardcoded credentials. Zero Kubernetes Secrets.
Identity proven by Kubernetes service account JWT only.
```

### Unauthorized Pod Output
```
=== Unauthorized Pod attempting Conjur access ===
Pod: unauth-demo | Service Account: unauthorized-sa

Attempting JWT authentication with unauthorized identity...
HTTP Response: 401

=== RESULT ===
ACCESS DENIED - 401 Unauthorized
Authorization boundary enforced by Conjur policy
Unauthorized identity cannot access protected secrets
```

## Related Projects

- [IAM Privilege Drift Detection Agent](https://github.com/IAM-AI-Security/IAM-Privilege-Drift-Agent)
- [NHI Lifecycle Automation Agent](https://github.com/IAM-AI-Security/NHI-Lifecycle-Automation-Agent)

