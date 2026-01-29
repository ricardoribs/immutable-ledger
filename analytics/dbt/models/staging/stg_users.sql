select
  id,
  name,
  email,
  cpf_last4,
  created_at,
  mfa_enabled
from {{ source('dw', 'users') }}
