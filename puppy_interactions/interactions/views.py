import logging

from django.http.response import JsonResponse, HttpResponse
from django.views.generic import View

from puppy_interactions.interactions.exceptions import UnrecognizedCommandException
from puppy_interactions.interactions.help_message import HELP_MESSAGE
from puppy_interactions.interactions.utils import (
    parse_webhook_text, do_create, do_logs, clear_logs
)

logger = logging.getLogger('puppy_interactions')


class InteractionView(View):
    def post(self, request, *args, **kwargs):
        try:
            try:
                text = request.POST.get("text")
                rater_uid = f"@{request.POST.get('user_id')}"
                command = parse_webhook_text(text)
            except UnrecognizedCommandException:
                data = HELP_MESSAGE
                data["text"] = "We don't know that one! Try these: "
                return JsonResponse(data=data)

            if command == "create":
                created_count = do_create(rater_user_id=rater_uid, text=text)
                data = {
                    "response_type": "ephemeral",
                    "text": f"We logged {created_count} interactions for you. Thanks!",
                }

            elif command == "logs":
                logs = do_logs(rater_user_id=rater_uid, text=text)
                if isinstance(logs, list):
                    data = {"response_type": "ephemeral",
                            "text": "These are some of your interaction logs!",
                            "attachments": [{"text": str(interaction)}
                                            for interaction in logs]}
                    data["attachments"].append(
                        {"text": "See more by adding an aggregation term"
                                 " like `/interactions 90 person`."})
                elif isinstance(logs, dict):
                    data = {
                        "response_type": "ephemeral",
                        "text": "These are your aggregated interaction logs!",
                        "attachments": [
                            {"text": f"{key}:: *positive* {stats['positive']} / *negative* {stats['negative']}"}
                            for key, stats in logs
                        ]
                    }
                else:
                    data = None

            elif command == "clear":
                clear_logs(rater_user_id=rater_uid)
                data = {"response_type": "ephemeral",
                        "text": "You're all clear. Thanks!"}

            elif command == "help":
                data = HELP_MESSAGE

            else:
                data = None

            return JsonResponse(data=data)

        except Exception as e:
            logger.exception("InteractionsView Exception!")
            return JsonResponse(data={"response_type": "ephemeral",
                                      "text": "Sorry, that didn't work. :-( "})

    def get(self, request, *args, **kwargs):
        return HttpResponse(status=200)
