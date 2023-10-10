from django.db.models.signals import pre_save
from django.dispatch import receiver
from context.models import e_ContextEvent


@receiver(pre_save, sender=e_ContextEvent)
def generate_tiffs(sender: e_ContextEvent, instance, **kwargs):
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass  # Object is new, so field hasn't technically changed, but you may want to do something else here.
    else:
        if obj.hasSimulation != instance.hasSimulation:  # Field has changed
            generate_tiffs.delay(obj.pk)
