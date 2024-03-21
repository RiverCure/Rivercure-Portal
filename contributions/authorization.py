from .models import e_ContextContribution

def author_of_contribution_check(user, contribution):
    """
    Checks if the user is the author of the Contribution
    """
    try:
        return e_ContextContribution.objects.filter(createdBy=user, pk=contribution.pk).exists() # TODO: Best way to do this query?
    except:
        return False