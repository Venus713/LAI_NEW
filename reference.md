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
- method: `GET`
- path: `ads/account_ads`
- payload:
```
{
    "fb_account_id": "***"
}
```
- headers: `Access-Token` required

2. get_html_code_for_ad_preview_handler
- method: `GET`
- path: `ads/html_code_for_ad_preview`
- payload:
```
{
    "creative_id": "***"
}
```
- headers: `Access-Token` required

3. import_ad_handler
- method: `POST`
- path: `ads/html_code_for_ad_preview`
- payload:
```
{
    "fb_account_id": "***",
    "ad_id": "***"
}
```
- headers: `Access-Token` required

4. update_ad_status_from_campaign_handler
- method: `PUT`
- path: `ads/ad_status_from_campaign`
- payload:
```
{
    "campaign_id": "***",
    "ad_name": "***",
    "status": "***"
}
```
- headers: `Access-Token` required

5. update_ad_status_handler
- method: `PUT`
- path: `ads/ad_status`
- payload:
```
{
    "ad_id": "***",
    "status": "***"
}
```
- headers: `Access-Token` required

6. ads_remove_ad_from_campaign_handler
- method: `DELETE`
- path: `ads/remove_ad`
- payload:
```
{
    "campaign_id": "***",
    "ad_creative_id": "***"
}
```
- headers: `Access-Token` required

7. get_ad_account_info_handler
- method: `GET`
- path: `ads/ad_account`
- payload:
```
{
    "fb_account_id": "***",
    "fb_account_name": "***"
}
```
- headers: `Access-Token` required

8. get_page_list_handler
- method: `GET`
- path: `ads/page_list`
- payload:
```
{
    "fb_account_id": "***",
    "fb_account_name": "***"
}
```
- headers: `Access-Token` required

9. get_page_list_handler
- method: `GET`
- path: `ads/page_list`
- payload: No required
- headers: `Access-Token` required

10. get_lead_forms_handler
- method: `GET`
- path: `ads/lead_forms`
- payload:
```
{
    "page_id": "***"
}
```
- headers: `Access-Token` required

11. get_account_ad_names_handler
- method: `GET`
- path: `ads/ad_names`
- payload:
```
{
    "fb_account_id": "***"
}
```
- headers: `Access-Token` required

12. get_insta_page_id_handler
- method: `GET`
- path: `ads/insta_page_id`
- payload:
```
{
    "page_id": "***"
}
```
- headers: `Access-Token` required

13. fb_get_active_adsets_handler
- method: `GET`
- path: `ads/active_adsets`
- payload:
```
{
    "campaign_id": "***"
}
```
- headers: `Access-Token` required

14. fb_create_single_image_ad_handler
- method: `post`
- path: `ads/single_image_ad`
- payload:
```
{
    'fb_account_id': '***,
    'page_id': '***,
    'instagram_actor_id': '***,
    'campaign_id': '***,
    'adset_id_list': '***,
    'call_to_action_type': '***,
    'image': '***,
    'ad_copy': '***,
    'ad_caption': '***,
    'url': '***,
    'ad_name': '***,
    'pixel_id': '***,
    'link_title': '***,
    'ad_description': '***,
    'deep_link': '***,
    'leadgen_form_id': '***,
    'acct_ad_names': '***,
    'creative_cache': '***
}
```
- headers: `Access-Token` required

15. fb_create_video_ad_handler
- method: `post`
- path: `ads/video_ad`
- payload:
```
{
    'fb_account_id': '***,
    'page_id': '***,
    'instagram_actor_id': '***,
    'campaign_id': '***,
    'adset_id_list': '***,
    'call_to_action_type': '***,
    'video_id': '***,
    'image': '***,
    'ad_copy': '***,
    'ad_caption': '***,
    'url': '***,
    'ad_name': '***,
    'pixel_id': '***,
    'link_title': '***,
    'ad_description': '***,
    'leadgen_form_name': '***,
}
```
- headers: `Access-Token` required

16. fb_create_video_ad_handler
- method: `post`
- path: `ads/video_ad`
- payload:
```
{
    'fb_account_id': '***,
    'page_id': '***,
    'instagram_actor_id': '***,
    'campaign_id': '***,
    'adset_id_list': '***,
    'call_to_action_type': '***,
    'video_id': '***,
    'image': '***,
    'ad_copy': '***,
    'ad_caption': '***,
    'url': '***,
    'ad_name': '***,
    'pixel_id': '***,
    'link_title': '***,
    'ad_description': '***,
    'leadgen_form_name': '***,
}
```
- headers: `Access-Token` required

17. copy_unimported_ad_handler
- method: `post`
- path: `ads/copy_ad`
- payload:
```
{
    'fb_account_id': '***,
    'campaign_id': '***,
    'ad_id': '***
}
```
- headers: `Access-Token` required

18. fb_create_post_ad_handler
- method: `post`
- path: `ads`
- payload:
```
{
    'fb_account_id': '***,
    'adset_id_list': '***,
    'campaign_id': '***,
    'page_id': '***,
    'post_id_list': '***,
    'name': '***,
    'pixel_id': '***,
    'instagram_id': '***
}
```
- headers: `Access-Token` required

19. fb_preview_single_image_ad_handler
- method: `get`
- path: `ads/single_image_ad`
- payload:
```
{
    'fb_account_id': '***,
    'instagram_actor_id': '***,
    'page_id': '***,
    'call_to_action_type': '***,
    'ad_name': '***,
    'image': '***,
    'ad_copy': '***,
    'ad_caption': '***,
    'url': '***,
    'link_title': '***,
    'ad_description': '***,
    'page_actor': '***,
    'leadgen_form_id': '***
}
```
- headers: `Access-Token` required

20. fb_create_video_ad_preview_handler
- method: `get`
- path: `ads/video_ad`
- payload:
```
{
    'fb_account_id': '***,
    'page_id': '***,
    'ad_name': '***,
    'image': '***,
    'ad_copy': '***,
    'ad_caption': '***,
    'call_to_action_type': '***,
    'video_id': '***,
    'url': '***, 'ad_description'
}
```
- headers: `Access-Token` required

21. fb_preview_copy_ad_handler
- method: `get`
- path: `ads/copy_ad`
- payload:
```
{
    'fb_account_id': '***,
    'ad_id': '***
}
```
- headers: `Access-Token` required

22. get_html_code_for_ad_preview_instagram_handler
- method: `get`
- path: `ads/html_code`
- payload:
```
{
    'creative_id': '***
}
```
- headers: `Access-Token` required

23. fb_create_post_ad_preview_handler
- method: `get`
- path: `ads`
- payload:
```
{
    'fb_account_id': '***,
    'page_id': '***,
    'post_id_list': '***,
    'instagram_id': '***
}
```
- headers: `Access-Token` required

24. upload_video_ad_handler
- method: `get`
- path: `ads/upload_video_ad`
- payload:
```
{
    'fb_account_id': '***,
    'filename': '***
}
```
- headers: `Access-Token` required

25. fb_preview_single_image_ad_newsfeed_handler
- method: `get`
- path: `ads/single_image_ad_newsfeed`
- payload:
```
{
    'fb_account_id': '***,
    'page_id': '***,
    'ad_name': '***,
    'image': '***,
    'ad_copy': '***,
    'ad_caption': '***,
    'call_to_action_type': '***,
    'instagram_actor_id': '***,
    'url': '***,
    'ad_description': '***,
    'link_title': '***,
    'page_actor': '***,
    'leadgen_form_id': '***
}
```
- headers: `Access-Token` required

26. fb_preview_single_image_ad_newsfeed_handler
- method: `get`
- path: `ads/single_image_ad_newsfeed`
- payload:
```
{
    'fb_account_id': '***,
    'page_id': '***,
    'ad_name': '***,
    'image': '***,
    'ad_copy': '***,
    'ad_caption': '***,
    'call_to_action_type': '***,
    'instagram_actor_id': '***,
    'url': '***,
    'ad_description': '***,
    'link_title': '***,
    'page_actor': '***,
    'leadgen_form_id': '***
}
```
- headers: `Access-Token` required


## fb_account apis
1. get_account_list_handler
- method: `get`
- path: `fb_accounts/`
- payload:
```
{
    'email': '***
}
```
- headers: `Access-Token` required

2. get_fb_insights_actions_w_data_handler
- method: `get`
- path: `fb_accounts/fb_insights_actions_w_data`
- payload:
```
{
    'fb_account_id': '***,
    'events_list': '***
}
```
- headers: `Access-Token` required

3. update_account_conversion_event_handler
- method: `put`
- path: `fb_accounts/conversion_event`
- payload:
```
{
    'fb_account_id': '***,
    'conversation_event': '***
}
```
- headers: `Access-Token` required

4. update_account_status_handler
- method: `put`
- path: `fb_accounts/status`
- payload:
```
{
    'fb_account_id': '***,
    'status': '***
}
```
- headers: `Access-Token` required
