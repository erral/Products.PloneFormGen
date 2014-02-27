from zope.globalrequest import getRequest
from Acquisition import aq_parent, aq_inner
from zope.component import adapter
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectMovedEvent
from Products.CMFPlone.interfaces import IFactoryTool
from Products.Archetypes.interfaces import IObjectInitializedEvent
from Products.PloneFormGen import PloneFormGenMessageFactory as _
from AccessControl import Unauthorized

from Products.PloneFormGen import interfaces

import zope.i18n


@adapter(interfaces.IPloneFormGenActionAdapter, IObjectAddedEvent)
def form_adapter_pasted(form_adapter, event):
    """If an action adapter is pasted into the form, add it to the form's
       list of active adapters. We only need to do anything if the action
       adapter isn't newly created in the portal_factory.
    """
    form_adapter = aq_inner(form_adapter)
    if IFactoryTool.providedBy(aq_parent(aq_parent(form_adapter))):
        return

    form = aq_parent(form_adapter)
    adapters = list(form.actionAdapter)
    if form_adapter.id not in adapters:
        adapters.append(form_adapter.id)
        form.setActionAdapter(adapters)


@adapter(interfaces.IPloneFormGenActionAdapter, IObjectMovedEvent)
def form_adapter_moved(form_adapter, event):
    """If an active action adapter is renamed, keep it active.

    Instead of renaming, some more moves are possible, like moving from
    one form to another, though that is unlikely.  We can handle it
    all though.

    Note that in a pure rename, event.oldParent is the same as
    event.newParent.  One of them could be None.  They may not always
    be forms.
    """
    form_adapter = aq_inner(form_adapter)
    if IFactoryTool.providedBy(aq_parent(aq_parent(form_adapter))):
        return

    if not event.oldParent:
        # We cannot know if the adapter was active, so we do nothing.
        pass
    try:
        adapters = list(event.oldParent.actionAdapter)
    except AttributeError:
        # no Form Folder, probably factory tool
        return
    was_active = event.oldName in adapters
    if was_active:
        # deactivate the old name
        adapters.remove(event.oldName)
        event.oldParent.setActionAdapter(adapters)
    if not was_active:
        # nothing to do
        return
    if event.newParent:
        try:
            adapters = list(event.newParent.actionAdapter)
        except AttributeError:
            # no Form Folder, probably factory tool
            return
        else:
            if event.newName not in adapters:
                adapters.append(event.newName)
                event.newParent.setActionAdapter(adapters)


@adapter(interfaces.IPloneFormGenForm, IObjectInitializedEvent)
def populate_pfg_on_creation(object, event):
    """ Create sample content that may help folks
        figure out how this gadget works.
    """
    request = getRequest()
    object.setSubmitLabel(zope.i18n.translate(_(u'pfg_formfolder_submit', u'Submit'), context=request))
    object.setResetLabel(zope.i18n.translate(_(u'pfg_formfolder_reset', u'Reset'), context=request))

    oids = object.objectIds()

    # if we have *any* content already, we don't need
    # the sample content
    if not oids:

        haveMailer = False
        # create a mail action
        try:
            object.invokeFactory('FormMailerAdapter', 'mailer')
            mailer = object['mailer']

            mailer.setTitle(zope.i18n.translate(
              _(u'pfg_mailer_title', u'Mailer'),
              context=request))
            mailer.setDescription(
              zope.i18n.translate(
                _(u'pfg_mailer_description',
                  u'E-Mails Form Input'),
                context=request))

            object._pfFixup(mailer)

            object.actionAdapter = ('mailer', )
            haveMailer = True
        except Unauthorized:
            logger.warn('User not authorized to create mail adapters. Form Folder created with no action adapter.')

        # create a replyto field
        object.invokeFactory('FormStringField', 'replyto')
        obj = object['replyto']
        obj.fgField.__name__ = 'replyto'

        obj.setTitle(zope.i18n.translate(
          _(u'pfg_replytofield_title', u'Your E-Mail Address'),
          context=request))

        obj.fgField.required = True
        obj.setFgStringValidator('isEmail')
        obj.setFgTDefault('here/memberEmail')
        obj.setFgDefault('dynamically overridden')

        object._pfFixup(obj)

        if haveMailer:
            mailer.replyto_field = 'replyto'

        # create a subject field
        object.invokeFactory('FormStringField', 'topic')
        obj = object['topic']
        obj.fgField.__name__ = 'topic'

        obj.setTitle(zope.i18n.translate(
          _(u'pfg_topicfield_title', u'Subject'),
          context=request))

        obj.fgField.required = True

        object._pfFixup(obj)

        if haveMailer:
            mailer.subject_field = 'topic'

        # create a comments field
        object.invokeFactory('FormTextField', 'comments')
        obj = object['comments']
        obj.fgField.__name__ = 'comments'

        obj.setTitle(zope.i18n.translate(
          _(u'pfg_commentsfield_title', u'Comments'),
          context=request))

        obj.fgField.required = True

        object._pfFixup(obj)

        # create a thanks page
        object.invokeFactory('FormThanksPage', 'thank-you')
        obj = object['thank-you']

        obj.setTitle(zope.i18n.translate(
          _(u'pfg_thankyou_title', u'Thank You'), context=request))
        obj.setDescription(zope.i18n.translate(
          _(u'pfg_thankyou_description', u'Thanks for your input.'),
          context=request))

        object._pfFixup(obj)

        object.thanksPage = 'thank-you'
