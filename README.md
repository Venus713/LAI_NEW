# LAI_NEW

## Pre-requisite
- Python3
- Virtualenv

## Install Package
- `npm` package install
```
$ npm install
```
- `pip` install
```
$ pip install -r requirements.txt
```

## Run on local
```
$ sls offline start
```

## Invoke Local
```
$ sls invoke local --function functionName --path **/**.json
```

## Deploy
```
$ PROFILE=AndrewColl sls deploy
```

## endpoints:
```
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/auth/signup
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/auth/confirm-signup
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/auth/confirm-fb
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/auth/resend-verification-code
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/auth/signin
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/auth/signout
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/auth/check-token
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/auth/changepassword
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/auth/forgotpassword
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/auth/confirm-forgotpassword
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/auth/users
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/auth/users/{id}
  PUT - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/auth/users/{id}
  DELETE - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/auth/users/{id}
  PUT - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/auth/users/{id}/disable
  PUT - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/auth/users/{id}/enable
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/campaigns_check_async
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/ad_account
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/run_auto_expansion
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/check_auto_expansion
  PUT - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/update_interests
  DELETE - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/hide_campaign
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/accounts_get_custom_audiences
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/importable_from_api
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/expansion_interests
  DELETE - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaigns/{id}
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/selectable_events
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/account_pixels
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/page_list
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/account_mobile_apps
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/active_audiences
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/fb_make_lookalikes
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/fb_targeting_simple
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/import_campaign
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/auto_expand
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/lead_forms
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/adsets
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/ad_names
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/current_billing_plan
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/status
  PUT - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/status_db
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/campaings/edit_fields
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/account_ads
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/html_code_for_ad_preview
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/import
  PUT - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/ad_status_from_campaign
  PUT - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/ad_status
  DELETE - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/remove_ad
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/ad_names
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/insta_page_id
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/active_adsets
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/single_image_ad
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/video_ad
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/copy_ad
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/single_image_ad
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/video_ad
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/copy_ad
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/html_code
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/upload_video_ad
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/ads/single_image_ad_newsfeed
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/fb_accounts/name_list
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/fb_accounts
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/fb_accounts
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/fb_accounts/fb_insights_actions_w_data
  PUT - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/fb_accounts/conversion_event
  PUT - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/fb_accounts/status
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/dashboard/adset_data
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/dashboard/changelog
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/dashboard/notifications
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/dashboard
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/dashboard/fb_insights_for_campaign
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/dashboard/fb_insights_for_account
  GET - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/dashboard/billing_plans
  POST - https://2h80rn6818.execute-api.us-east-1.amazonaws.com/dev/dashboard/subscribe_plan
```
## functions:
``- `
  - signup: lai-new-dev-signup
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
  - disable_user: lai-new-dev-disable_user
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
  - get_account_ads: lai-new-dev-get_account_ads
  - get_html_code_for_ad_preview: lai-new-dev-get_html_code_for_ad_preview
  - import_ad: lai-new-dev-import_ad
  - update_ad_status_from_campaign: lai-new-dev-update_ad_status_from_campaign
  - update_ad_status: lai-new-dev-update_ad_status
  - ads_remove_ad_from_campaign: lai-new-dev-ads_remove_ad_from_campaign
  - get_account_ad_names: lai-new-dev-get_account_ad_names
  - get_insta_page_id: lai-new-dev-get_insta_page_id
  - fb_get_active_adsets: lai-new-dev-fb_get_active_adsets
  - fb_create_single_image_ad: lai-new-dev-fb_create_single_image_ad
  - fb_create_video_ad: lai-new-dev-fb_create_video_ad
  - copy_unimported_ad: lai-new-dev-copy_unimported_ad
  - fb_create_post_ad: lai-new-dev-fb_create_post_ad
  - fb_preview_single_image_ad: lai-new-dev-fb_preview_single_image_ad
  - fb_create_video_ad_preview: lai-new-dev-fb_create_video_ad_preview
  - fb_preview_copy_ad: lai-new-dev-fb_preview_copy_ad
  - get_html_code_for_ad_preview_instagram: lai-new-dev-get_html_code_for_ad_preview_instagram
  - fb_create_post_ad_preview: lai-new-dev-fb_create_post_ad_preview
  - upload_video_ad: lai-new-dev-upload_video_ad
  - fb_preview_single_image_ad_newsfeed: lai-new-dev-fb_preview_single_image_ad_newsfeed
  - get_account_name_list: lai-new-dev-get_account_name_list
  - add_all_fb_accounts: lai-new-dev-add_all_fb_accounts
  - get_account_list: lai-new-dev-get_account_list
  - get_fb_insights_actions_w_data: lai-new-dev-get_fb_insights_actions_w_data
  - update_account_conversion_event: lai-new-dev-update_account_conversion_event
  - update_account_status: lai-new-dev-update_account_status
  - get_adset_data: lai-new-dev-get_adset_data
  - get_changelog: lai-new-dev-get_changelog
  - get_notifications: lai-new-dev-get_notifications
  - get_account_sidebar_and_dashboard_info: lai-new-dev-get_account_sidebar_and_dashboard_info
  - get_fb_insights_for_campaign: lai-new-dev-get_fb_insights_for_campaign
  - get_fb_insights_for_account: lai-new-dev-get_fb_insights_for_account
  - get_available_billing_plans: lai-new-dev-get_available_billing_plans
  - subscribe_to_plan: lai-new-dev-subscribe_to_plan
```