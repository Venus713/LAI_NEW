# Tabels
1. PK
- User
- FB_Account, sk = str(fb_account_id) + '-' + str(user_id)
- Campaign
- Campaign_Ad
- Ads
- AsyncResult
- FB_Exp_Interests


# TEST
## Auth apis

1. signup
- method: post
- payload:
```
{
    "username": "***",
    "email": "***",
    "password": "***",
    "role": "***" ('admin' or 'customer')
}
```

2. resend_verification_code
- method: post
- payload:
```
{
    "email": "***"
}
```

3. confirm_signup
- method: post
- payload:
```
{
    "user_id": "***",
    "fb_access_token": "***"
}
```
- headers:
```
{"Access-Token": "***"}
```

4. signin
- method: post
- payload:
```
{
    "email": "***",
    "password": "***"
}
```

5. checktoken
- method: get
- headers:
```
{
    "Access-Token": "***"
}
```

6. confirm_facebook
- method: post
- payload:
```
{
    "user_id": "***",
    "fb_access_token": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

7. change_password
- method: post
- payload:
```
{
    "email": "***",
    "previous_pass": "***",
    "proposed_pass": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

8. forgot_password
- method: post
- payload:
```
{
    "email": "***"
}
```

9. confirm_forgotpassword
- method: post
- payload:
```
{
    "email": "***",
    "password": "***",
    "code": "***"
}
```

10. userlist
- method: get
- headers:
```
{
    "Access-Token": "***"
}
```

11. retrieve_user
- method: get
- query params: <user_id>
- headers:
```
{
    "Access-Token": "***"
}
```

12. update_user
- method: put
- params: <user_id>
- payload:
```
{
    "first_name": "***",
    "last_name": "***",
    ...
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

13. delete_user
- method: delete
- params: <user_id>
- headers:
```
{
    "Access-Token": "***"
}
```

14. enable_user
- method: post
- params: <user_id>
- headers:
```
{
    "Access-Token": "***"
}
```

## Campaign_apis
1. get_selectable_events_handler
- method: get
- path: `campaings/selectable_events/`
- payload:
```
{
    "fb_account_id": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

2. account_pixels
- method: get
- path: `campaings/account_pixels/`
- payload:
```
{
    "fb_account_id": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

3. account_mobile_apps_handler
- method: get
- path: `campaings/account_mobile_apps/`
- payload:
```
{
    "fb_account_id": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

4. get_page_list_handler
- method: get
- path: `campaings/page_list/`
- headers:
```
{
    "Access-Token": "***"
}
```

5. active_audiences_handler
- method: get
- path: `campaings/active_audiences/`
- payload:
```
{
    "fb_account_id": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

6. fb_make_lookalikes_handler
> NOTE: didn't test this api because I don't have a correct audience_id.
- method: get
- path: `campaings/fb_make_lookalikes/`
- payload:
```
{
    "fb_account_id": "***",
    "audience_id": "***",
    "country": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

7. create_campaign
- method: post
- path: `campaings/`
- payload:
```
{
    "fb_account_id": "***",
    "campaign_name": "***",
    "daily_budget": "***",
    "campaign_objective": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

8. create_fb_targeting_simple_handler
> NOTE: I need the correct parameters for testing.
- method: post
- path: `campaings/fb_targeting_simple/`
- payload:
```
{
    "fb_account_id": "***",
    "campaign_id": "***",
    "page_id": "***",
    "app_url": "***",
    "interests": "***",
    "audience_list": "***",
    "gender": "***",
    "min_age": "***",
    "max_age": "***",
    "country": "***",
    "conversion_event": "***",
    "pixel_id": "***",
    "max_number_of_ads": "***",
    "adset_to_copy_targeting": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

9. import_campaign
- method: post
- path: `campaings/import_campaign/`
- payload:
```
{
    "fb_account_id": "***",
    "campaign_id": "***",
    "campaign_name": "***",
    "conversion_event": "***",
    "campaign_type": "***",
    "cpa_goal": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

10. auto_expand
- method: get
- path: `campaings/auto_expand/`
- payload:
```
{
    "fb_account_id": "***",
    "campaign_id": "***",
    "status": "***",
    "conversion_event_name": "***",
    "daily_budget": "***",
    "cac": "***",
    "number_of_adsets": "***",
    "name_template": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

11. get_lead_forms
- method: get
- path: `campaings/lead_forms/`
- payload:
```
{
    "page_id": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

12. campaigns_get_adsets
- method: get
- path: `campaings/adsets/`
- payload:
```
{
    "campaign_id": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

13. get_ad_names
- method: get
- path: `campaings/ad_names/`
- payload:
```
{
    "fb_account_id": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

14. get_current_billing_plan
- method: get
- path: `campaings/current_billing_plan/`
- headers:
```
{
    "Access-Token": "***"
}
```

15. get_fb_campaign_status
- method: get
- path: `campaings/status/`
- payload:
```
{
    "campaign_id": "***",
    "preloaded_campaign_object": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

16. update_campaign_status_db
- method: put
- path: `campaings/status_db/`
- payload:
```
{
    "fb_account_id": "***",
    "campaign_id": "***",
    "fb_status": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

17. edit_fields
- method: post
- path: `campaings/edit_fields/`
- payload:
```
{
    "changes": "***",
    "campaign_id": "***",
    "originals": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

18. campaigns_check_async
- method: post
- path: `campaings/campaigns_check_async/`
- payload:
```
{
    "account_id": "***",
    "asyncs": [{'campaign_id': ***, 'task_id': ***}, ...]
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

19. get_ad_account_info
- method: get
- path: `campaings/ad_account_info/`
- payload:
```
{
    "fb_account_id": "***",
    "fb_account_name": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

20. run_auto_expansion
- method: post
- path: `campaings/run_auto_expansion/`
- payload:
```
{
    "fb_account_id": "***",
    "campaign_id": "***",
    "maximum_number_adesets": "***",
    "starting_interest_list": [***]
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

21. check_auto_expansion
- method: get
- path: `campaings/check_auto_expansion/`
- payload:
```
{
    "task_id": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

22. update_interests
- method: put
- path: `campaings/update_interests/`
- payload:
```
{
    "campaign_id": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

23. hide_campaign
- method: delete
- path: `campaings/hide_campaign/`
- payload:
```
{
    "campaign_id": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

24. accounts_get_custom_audiences
- method: get
- path: `campaings/accounts_get_custom_audiences/`
- payload:
```
{
    "fb_account_id": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

25. get_importable_from_api
- method: get
- path: `campaings/importable_from_api/`
- payload:
```
{
    "fb_account_id": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

26. get_expansion_interests
- method: get
- path: `campaings/expansion_interests/`
- payload:
```
{
    "fb_account_id": "***",
    "campaign_id": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

27. campain_list
- method: get
- path: `campaings/`
- payload:
```
{
    "fb_account_id": "***",
    "campaign_id": "***"
}
```
- headers:
```
{
    "Access-Token": "***"
}
```

## Ads apis
1. get_account_ads_handler