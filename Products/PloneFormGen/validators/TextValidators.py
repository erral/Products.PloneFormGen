from Products.validation import validation, interfaces

class LinkSpamValidator:
    """ Validates whether or not a string has anything that seems link-like. For
    these purposes, we're considering the following fragments to be linky:
        "<a "
        "www"
        "http"
        ".com"
        (See Products.PloneFormGen.config's stringValidators for an unfortunate
        repeat of this logic.)
    """

    __implements__ = (interfaces.ivalidator,)

    name = 'LinkSpamValidator'

    def __init__(self, name, title='', description=''):
        self.name = name
        self.title = title or name
        self.description = description

    def __call__(self, value, *args, **kwargs):
        # validation is optional and configured on the field
        obj = kwargs.get('instance')
        if not obj:
            return 1
        vfield = obj.Schema().get('validateNoLinkSpam')
        if vfield is None:
            return 1
        validate = vfield.getAccessor(kwargs.get('instance'))()
        if not validate:
            return 1
        bad_signs = ("<a ",
                     "www.",
                     "http:",
                     ".com",
                     )
        value = value.lower()
        for s in bad_signs:
            if s in value:
                return ("Validation failed(%(name)s): links are not allowed." %
                        { 'name' : self.name, })
        return 1

validation.register(LinkSpamValidator('isNotLinkSpam'))