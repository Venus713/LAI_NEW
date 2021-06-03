import datetime

from utils.logging import logger


def event_list_to_string(event):
    if event and isinstance(event, list):
        if event[1] == 'custom_conversion':
            event = 'offsite_conversion.custom.{}'.format(event[0])
        else:
            event = event[0]
    return event


def get_fb_insights_actions_w_data(account_id, obj, events_list):
    events_to_check = []
    for e in events_list:
        events_to_check.append(event_list_to_string(e[1]).upper())

    try:
        now = datetime.datetime.now()
        dates = [
            {
                'since': (
                    now - datetime.timedelta(days=i)).strftime("%Y-%m-%d"),
                'until': (
                    now - datetime.timedelta(days=i)).strftime("%Y-%m-%d"),
            }
            for i in range(14, 0, -1)
        ]

        insights = obj.get_insights(
            params={'time_ranges': dates},
            fields=['spend', 'date_start', 'impressions', 'actions']
        )

        def get_conversions(actions, action_set):
            for a in actions:
                if len(a['value']) > 0:
                    if int(a['value']) > 0:
                        action_set.add(a['action_type'].upper())

        action_set = set()
        for i in insights:
            get_conversions(i['actions'], action_set)

        events_with_data = []
        for a in action_set:
            if a in events_to_check:
                events_with_data.append(a)

        return events_with_data

    except Exception as e:
        logger.exception(f'Exception in get_fb_insights_actions_w_data: {e}')
        return []
