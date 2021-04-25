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
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaings
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaigns/{id}
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaigns/search/{key}
  PUT - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaigns/{id}
  DELETE - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaigns/{id}
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaigns/fb
  GET - https://yfvlcj50xd.execute-api.us-east-1.amazonaws.com/dev/campaigns/graph
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
  - campain_list: lai-new-dev-campain_list
  - retrieve_campaign: lai-new-dev-retrieve_campaign
  - search_campaign: lai-new-dev-search_campaign
  - update_campaign: lai-new-dev-update_campaign
  - delete_campaign: lai-new-dev-delete_campaign
  - campaign_from_facebook: lai-new-dev-campaign_from_facebook
  - campaign_performance: lai-new-dev-campaign_performance
```