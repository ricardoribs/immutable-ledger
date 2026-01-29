select
  u.id as user_id,
  u.name,
  u.email,
  u.cpf_last4,
  u.created_at as customer_since,
  u.mfa_enabled,
  k.status as kyc_status,
  k.risk_level,
  k.created_at as kyc_created_at
from {{ ref('stg_users') }} u
left join {{ ref('stg_kyc_profiles') }} k on k.user_id = u.id
