select
  id,
  user_id,
  status,
  risk_level,
  created_at
from {{ source('dw', 'kyc_profiles') }}
