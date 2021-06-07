from facebook_business.exceptions import FacebookRequestError


def get_active_fb_events(account):
    try:
        insights = account.get_insights(fields=['actions'])

        actions = set()
        for insight in insights:
            for action in insight['actions']:
                actions.add(action['action_type'])

        action_list = list(actions)
        action_list.sort()
        return action_list

    # Can fail because of insights request, insights[0],
    #  or insights[0]['actions']
    except (FacebookRequestError, IndexError, KeyError):
        return ['impressions', 'clicks']


def event_list_to_string(event):
    if event is not None and isinstance(event, list):
        if event[1] == 'custom_conversion':
            event = f'offsite_conversion.custom.{event[0]}'
        else:
            event = event[0]
    return event
