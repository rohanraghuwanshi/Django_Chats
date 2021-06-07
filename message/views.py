from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import Message, MessageAttachment, MessageSerializer

# Create your views here.


class MessageView(ModelViewSet):
    queryset = Message.objects.select_related("sender", "reciever").prefetch_related(
        "message_attachments"
    )
    serializer_class = MessageSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):

        attachments = request.data.pop("attachments", None)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if attachments:
            MessageAttachment.objects.bulk_create(
                [
                    MessageAttachment(**attachment, message_id=serializer.data["id"])
                    for attachment in attachments
                ]
            )

            message_data = self.get_queryset().get(id=serializer.data["id"])

            return Response(self.serializer_class(message_data).data, status=201)

        return Response(serializer.data, status=201)