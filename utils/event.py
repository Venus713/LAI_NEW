from facebook_business.adobjects.customconversion import CustomConversion


def get_promoted_object(
    api, custom_event, user_os, application_id, object_store_url
):
    custom_event_name, custom_event_type = custom_event
    if custom_event_type == "custom_event":
        return {
            'pixel_id': application_id,
            'custom_event_type': 'OTHER',
            'pixel_rule': {
                'event': {'eq': custom_event_name},
            }
        }

    elif custom_event_type == "custom_conversion":
        cc = CustomConversion(custom_event_name, api)
        cc.remote_read(fields=['rule'])
        return {
            'pixel_id': application_id,
            'custom_event_type': 'OTHER',
            'pixel_rule': cc['rule']
        }

    # Default type
    # ####### NEED TO UPDATE THIS FOR MOBILE APPS
    elif user_os:
        promoted_object = {
            'application_id': application_id,
            'object_store_url': object_store_url,
            'custom_event_type': custom_event_name,
        }
        return promoted_object

    else:
        return {
            'custom_event_type': custom_event_name,
            'pixel_id': application_id,
        }
