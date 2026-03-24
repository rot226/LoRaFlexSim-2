# Coverage of specialized modules

The table below summarizes automated tests (unit or integration) that cover advanced modules used by the validation matrix. Each row lists the corresponding matrix scenario and the automated checks that validate that module.

| Module | Matrix scenario | Automated tests | Status |
| --- | --- | --- | --- |
| Duty cycle | `duty_cycle_enforcement_class_a` | `test_poisson_independence.py`, validation matrix | ✅ |
| Dynamic multichannel | `dynamic_multichannel_random_assignment` | `test_multichannel_selection.py`, `test_mobility_multichannel_integration.py`, validation matrix | ✅ |
| Mobile Class B | `class_b_mobility_multichannel` | `test_class_bc.py`, validation matrix | ✅ |
| Mobile Class C | `class_c_mobility_multichannel` | `test_mobility_multichannel_integration.py`, validation matrix | ✅ |
| EXPLoRa-AT | `explora_at_balanced_airtime` | `loraflexsim/launcher/tests/test_explora_at.py`, validation matrix | ✅ |
| ADR-ML | `adr_ml_adaptive_strategy` | `loraflexsim/launcher/tests/test_adr_ml.py`, validation matrix | ✅ |

Scenario presence is automatically checked by `test_validation_matrix_covers_specialised_modules`, which fails if one of the modules above is no longer represented.

Detailed scenario references:
- `loraflexsim/validation/__init__.py` for the exact configuration of each case.
- The tests listed above document the module-specific validation logic.
