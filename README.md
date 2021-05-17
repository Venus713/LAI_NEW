# LAI_NEW

## endpoints:
```
  POST - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/auth/signup
  POST - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/auth/confirm-signup
  POST - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/auth/confirm-fb
  POST - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/auth/resend-verification-code
  POST - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/auth/signin
  POST - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/auth/signout
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/auth/check-token
  POST - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/auth/changepassword
  POST - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/auth/forgotpassword
  POST - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/auth/confirm-forgotpassword
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/auth/users
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/auth/users/{id}
  PUT - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/auth/users/{id}
  DELETE - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/auth/users/{id}
  POST - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/auth/users/{id}
  POST - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings
  POST - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/campaigns_check_async
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/ad_account_info
  POST - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/run_auto_expansion
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/check_auto_expansion
  PUT - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/update_interests
  DELETE - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/hide_campaign
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/accounts_get_custom_audiences
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/importable_from_api
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/expansion_interests
  DELETE - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaigns/{id}
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/selectable_events
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/account_pixels
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/page_list
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/account_mobile_apps
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/active_audiences
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/fb_make_lookalikes
  POST - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/fb_targeting_simple
  POST - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/import_campaign
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/auto_expand
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/lead_forms
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/adsets
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/ad_names
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/current_billing_plan
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/status
  PUT - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/status_db
  POST - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings/edit_fields

```
## functions:
```
  - signup: lai-new-dev-signup
  - custom_message: lai-new-dev-custom_message
  - confirm_signup: lai-new-dev-confirm_signup
  - confirm_facebook: lai-new-dev-confirm_facebook
  - resend_verification_code: lai-new-dev-resend_verification_code
  - signin: lai-new-dev-signin
  - signout: lai-new-dev-signout
  - checktoken: lai-new-dev-checktoken
  - change_password: lai-new-dev-change_password
  - forgot_password: lai-new-dev-forgot_password
  - confirm_forgotpassword: lai-new-dev-confirm_forgotpassword
  - userlist: lai-new-dev-userlist
  - retrieve_user: lai-new-dev-retrieve_user
  - update_user: lai-new-dev-update_user
  - delete_user: lai-new-dev-delete_user
  - enable_user: lai-new-dev-enable_user
  - create_campaign: lai-new-dev-create_campaign
  - campaigns_check_async: lai-new-dev-campaigns_check_async
  - get_ad_account_info: lai-new-dev-get_ad_account_info
  - run_auto_expansion: lai-new-dev-run_auto_expansion
  - check_auto_expansion: lai-new-dev-check_auto_expansion
  - update_interests: lai-new-dev-update_interests
  - hide_campaign: lai-new-dev-hide_campaign
  - accounts_get_custom_audiences: lai-new-dev-accounts_get_custom_audiences
  - get_importable_from_api: lai-new-dev-get_importable_from_api
  - get_expansion_interests: lai-new-dev-get_expansion_interests
  - delete_campaign: lai-new-dev-delete_campaign
  - campain_list: lai-new-dev-campain_list
  - get_selectable_events: lai-new-dev-get_selectable_events
  - account_pixels: lai-new-dev-account_pixels
  - get_page_list: lai-new-dev-get_page_list
  - account_mobile_apps: lai-new-dev-account_mobile_apps
  - active_audiences: lai-new-dev-active_audiences
  - fb_make_lookalikes: lai-new-dev-fb_make_lookalikes
  - create_fb_targeting_simple: lai-new-dev-create_fb_targeting_simple
  - import_campaign: lai-new-dev-import_campaign
  - auto_expand: lai-new-dev-auto_expand
  - get_lead_forms: lai-new-dev-get_lead_forms
  - campaigns_get_adsets: lai-new-dev-campaigns_get_adsets
  - get_ad_names: lai-new-dev-get_ad_names
  - get_current_billing_plan: lai-new-dev-get_current_billing_plan
  - get_fb_campaign_status: lai-new-dev-get_fb_campaign_status
  - update_campaign_status_db: lai-new-dev-update_campaign_status_db
  - edit_fields: lai-new-dev-edit_fields
  - execute_async_task: lai-new-dev-execute_async_task
```