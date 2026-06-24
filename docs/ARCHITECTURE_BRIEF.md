# Secrets Without Secrets: Why Kubernetes Workload Identity Requires a Vault-Backed JWT Architecture

**Go Cloud Architects | Architecture Brief**
© 2026 Go Cloud Architects — curtis@igasecurityconsulting.com

---

## The Business Problem

Hardcoded credentials in containerized applications are one of the most well-documented security failures in cloud-native engineering. Security teams have been warning developers about this practice for years. The warnings have not worked. The GitGuardian State of Secrets Sprawl 2026 report found 28.65 million hardcoded secrets were added to public GitHub repositories in 2025 alone a 34% year-over-year increase. The awareness exists. The behavior has not changed.

The reason the warnings have not worked is that the proposed alternatives are worse from a developer experience perspective. Kubernetes Secrets are the default replacement for hardcoded credentials, and they fail on the same terms. A Kubernetes Secret is base64 encoded, not encrypted. Any user or service account with kubectl read access to the namespace can retrieve it. Any application running in the namespace can mount it. The secret is at rest in etcd, accessible through the Kubernetes API, and outside the PAM governance boundary entirely. Security teams running CyberArk have no visibility into credentials stored in Kubernetes Secrets because those credentials were never onboarded into the vault.

Environment variables are marginally better than baking credentials into the container image and substantially worse than a secrets management solution. They are visible in pod specs, logged in crash dumps, accessible through the container runtime, and static. A credential delivered as an environment variable at pod startup is the same credential for the lifetime of the pod, whether that pod runs for five minutes or five months.

The underlying problem is not developer negligence. It is that the standard Kubernetes credential delivery mechanisms Secrets and environment variables are not secrets management. They are credential storage with insufficient access controls and no lifecycle management. The CyberArk Federal agencies whitepaper makes this point directly: secrets management must enable the organization to defend against attacks by centrally managing and securing secrets for all application types across the enterprise. Kubernetes workloads are application types. They are not currently in scope for most enterprise PAM programs.

---

## Why Existing Approaches Fall Short

The standard enterprise response to Kubernetes credentials sprawl is one of three approaches, and all three leave application credentials outside the vault.

The first is secrets scanning in CI/CD pipelines. TruffleHog, GitLeaks, and similar tools detect hardcoded credentials before they reach production. This is a necessary control and an insufficient one. It catches credentials that developers accidentally commit. It says nothing about credentials that are deliberately stored in Kubernetes Secrets or environment variables because the developer had no better option. Scanning the pipeline does not change the delivery mechanism.

The second is Kubernetes Secrets encryption at rest. Enabling etcd encryption for Kubernetes Secrets addresses one attack vector direct etcd access while leaving every other access vector intact. An encrypted Kubernetes Secret is still accessible through the Kubernetes API to any service account with read permissions. It is still mounted as a plain-text environment variable in the pod. Encryption at rest is a compliance checkbox. It is not a secrets governance model.

The third is cloud provider secrets integration. AWS Secrets Manager, Azure Key Vault, and GCP Secret Manager are mature secrets management platforms. They integrate with Kubernetes through the External Secrets Operator or similar tools and are a legitimate improvement over native Kubernetes Secrets. What they do not provide is the centralized PAM governance model, the unified audit trail across cloud providers, and the policy-based authorization that CyberArk Conjur delivers for organizations that have already invested in enterprise PAM.

---

## The Architectural Position

The JWT authenticator pattern implemented in this project eliminates static credentials from the workload delivery path entirely. The pod never receives a credential it stores. It receives a credential it uses and discards.

When a Kubernetes pod starts, it presents its native service account JWT token which Kubernetes automatically mounts to the Conjur authn-jwt endpoint. Conjur validates the JWT signature against the Kubernetes OIDC public keys, verifies that the service account identity matches an authorized host in Conjur policy, and returns a short-lived Conjur access token. The pod uses that access token to retrieve the application secret from the Conjur vault. The secret is delivered at runtime, used by the application, and never persisted in the container image, environment variables, or Kubernetes Secrets.

The authorization boundary is enforced at the Conjur policy layer. An unauthorized pod one whose service account is not listed in the Conjur host identity policy receives a 401 denial. Not a timeout. Not a silent failure. An explicit policy enforcement response. This is the ZSP proof: the authorized pod gets the secret, the unauthorized pod gets the 401, and the Conjur audit log records both outcomes.

---

## Design Principles

**Identity-based authentication, not credential-based.** The pod proves who it is using its Kubernetes service account identity. It does not present a password, API key, or certificate. The Kubernetes platform is the identity provider. Conjur is the authorization engine.

**Dynamic delivery, not static storage.** Secrets are retrieved at runtime and never persisted in the pod. A credential that is not stored cannot be stolen from storage. A credential that expires after use cannot be replayed.

**Policy-as-code authorization.** The Conjur host identity policy defines exactly which service accounts can access which secrets. The policy is version-controlled, auditable, and enforced at the vault layer regardless of what Kubernetes RBAC allows. The vault is the final authorization boundary.

**Zero trust for workloads.** Every pod that needs a secret must authenticate. There are no shared credentials, no namespace-wide grants, and no implicit trust based on network location. Each service account gets the minimum access its application requires.

---

## Security Controls

| Control | Implementation | Purpose |
|---|---|---|
| JWT-based workload authentication | Kubernetes service account JWT validated by Conjur | No static credentials required for vault access |
| Policy-based authorization | Conjur host identity policy per service account | Fine-grained access control at the vault layer |
| 401 enforcement for unauthorized pods | Conjur policy denial | Explicit boundary enforcement, not silent failure |
| Zero Kubernetes Secrets | No application credentials stored in etcd | Removes Kubernetes API as an access vector |
| Audit trail per secret retrieval | Conjur audit log per authenticated request | Complete retrieval history for compliance examination |
| Short-lived access tokens | Conjur access token per authentication | Limits replay window if token is intercepted |

---

## Compliance Mapping

| Control Objective | Framework | Implementation |
|---|---|---|
| Eliminate hardcoded credentials | OWASP LLM06 Excessive Agency | Zero credentials in container image or environment variables |
| Centralized secrets management | NIST IA-5 Authenticator Management | All application secrets managed in Conjur vault |
| Least privilege secret access | NIST AC-3 Access Enforcement | Conjur policy grants minimum required access per service account |
| Audit trail for secret retrieval | SOX ITGC | Conjur audit log per retrieval, exportable for examination |
| Workload identity verification | NIST SP 800-207 Zero Trust | Every pod authenticated before secret delivery |
| Non-human identity governance | FFIEC IT Examination Handbook | Application credentials within PAM governance boundary |

---

## Business Impact

The operational case for JWT-based secrets delivery is the onboarding simplicity relative to alternative approaches. The Kubernetes service account JWT is automatically mounted by the platform. The application requires no changes to its credential consumption model beyond pointing to the Conjur endpoint instead of an environment variable. The security team gains PAM visibility into application credentials without requiring developer workflow changes.

The compliance case is PAM scope extension. Organizations running CyberArk for privileged human access have an established vault, rotation policies, and audit trail infrastructure. Application credentials stored in Kubernetes Secrets are outside that scope entirely. JWT-based Conjur authentication brings application credentials into the existing PAM governance model without a separate tooling investment.

The security case is the elimination of the static credential attack surface. A credential that is never stored cannot be stolen from storage. The only attack vectors against a JWT-authenticated Conjur deployment are the Kubernetes service account token itself which is platform-managed and short-lived and the Conjur vault which is the intended target of enterprise PAM investment.

---

## Enterprise Extension

This implementation uses Conjur OSS. Enterprise deployment extends the same pattern to CyberArk Conjur Enterprise with the following additions:

High availability through Conjur Enterprise clustering eliminates the single-point-of-failure that OSS presents in production environments. Policy synchronization across followers ensures that authorization policy changes propagate consistently across the deployment. Integration with CyberArk Privileged Access Manager provides a unified audit trail across human privileged access and application secret retrieval. The authn-jwt authenticator pattern is identical between OSS and Enterprise the architecture demonstrated here is directly portable to an enterprise deployment.

---

## Future Roadmap

**Phase 2: Multi-Cluster Federation**
Extend the JWT authenticator pattern across multiple Kubernetes clusters using a shared Conjur Enterprise deployment. Each cluster authenticates using its own OIDC endpoint. A unified Conjur policy governs secret access across all clusters from a single control plane.

**Phase 3: Secrets Rotation Integration**
Integrate with CyberArk CPM for automated rotation of the application credentials stored in Conjur. Rotation events invalidate cached credentials and force re-retrieval at the next pod authentication cycle. The application sees no interruption. The credential lifetime is bounded by the rotation policy.

**Phase 4: Service Mesh Integration**
Extend the zero-trust workload identity pattern to mTLS between services using Conjur-issued certificates. Each service authenticates using its JWT identity, receives a short-lived certificate, and presents that certificate for service-to-service communication. This completes the ZSP pattern from secret delivery to inter-service authentication.

---

*Sources: GitGuardian State of Secrets Sprawl 2026; CyberArk Protect Federal Agencies by Securing DevOps, Secrets and Other Non-Human Identities; NIST SP 800-207 Zero Trust Architecture; NIST CSF 2.0; OWASP LLM Top 10 2025; FFIEC IT Examination Handbook.*
