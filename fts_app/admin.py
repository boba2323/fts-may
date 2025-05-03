from django.contrib import admin
from fts_app.models import File, Tag, Modification, Folder, ActionLog
# Register your models here.

class FileAdmin(admin.ModelAdmin):
    pass

class ActionLogAdmin(admin.ModelAdmin):
    pass

class TagAdmin(admin.ModelAdmin):
    pass

class ModifAdmin(admin.ModelAdmin):
    pass

class FolderAdmin(admin.ModelAdmin):
    pass


admin.site.register(File, FileAdmin)
admin.site.register(Tag, FileAdmin)
admin.site.register(Modification, FileAdmin)
admin.site.register(Folder, FileAdmin)
admin.site.register(ActionLog, FileAdmin)
