from django.db.models.signals import pre_save
from django.dispatch import receiver
from context.models import e_ContextEvent
from rivercureproject.celery import app


@receiver(pre_save, sender=e_ContextEvent)
def generate_tiffs_signal(sender: e_ContextEvent, instance, **kwargs):
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass  # Object is new, so field hasn't technically changed, but you may want to do something else here.
    else:
        if obj.hasSimulation != instance.hasSimulation and instance.hasSimulation == True:  # Field has changed
            app.send_task('context.tasks.generate_tiffs', args=(obj.pk, ))
