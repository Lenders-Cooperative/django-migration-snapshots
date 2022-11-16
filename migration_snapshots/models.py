import os

from dateutil.parser import parse
from django.core.files import File
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext as _

from . import settings
from .utils import MigrationHistoryUtil

if settings.MIGRATION_SNAPSHOT_MODEL is True:

    class MigrationSnapshot(models.Model):
        BMP = "bmp"
        CGIMAGE = "cgimage"
        DOT_CANON = "canon"
        DOT = "dot"
        GV = "gv"
        XDOT = "xdot"
        XDOT12 = "xdot1.2"
        XDOT14 = "xdot1.4"
        EPS = "eps"
        EXR = "exr"
        FIG = "fig"
        GD = "gd"
        GD2 = "gd2"
        GIF = "gif"
        GTK = "gtk"
        ICO = "ico"
        CMAP = "cmap"
        ISMAP = "ismap"
        IMAP = "imap"
        CMAPX = "cmapx"
        IMAGE_NP = "imap_np"
        CMAPX_NP = "cmapx_np"
        JPG = "jpg"
        JPEG = "jpeg"
        JPE = "jpe"
        JPEG_2000 = "jp2"
        JSON = "json"
        JSON0 = "json0"
        DOT_JSON = "dot_json"
        XDOT_JSON = "xdot_json"
        PDF = "pdf"
        PIC = "pic"
        PICT = "pct"
        APPLE_PICT = "pict"
        PLAIN_TEXT = "plain"
        PLAIN_EXT = "plain-ext"
        PNG = "png"
        POV_RAY = "pov"
        PS_PDF = "ps2"
        PSD = "psd"
        SGI = "sgi"
        SVG = "svg"
        SVGZ = "svgz"
        TGA = "tga"
        TIF = "tif"
        TIFF = "tiff"
        TK = "tk"
        VML = "vml"
        VMLZ = "vmlz"
        VRML = "vrml"
        WBMP = "wbmp"
        WEBP = "webp"
        XLIB = "xlib"
        X11 = "x11"

        FORMAT_CHOICES = [
            (BMP, BMP.upper()),
            (CGIMAGE, CGIMAGE.upper()),
            (DOT_CANON, DOT_CANON.upper()),
            (DOT, DOT.upper()),
            (GV, GV.upper()),
            (XDOT, XDOT.upper()),
            (XDOT12, XDOT12.upper()),
            (XDOT14, XDOT14.upper()),
            (EPS, EPS.upper()),
            (EXR, EXR.upper()),
            (FIG, FIG.upper()),
            (GD, GD.upper()),
            (GD2, GD2.upper()),
            (GIF, GIF.upper()),
            (GTK, GTK.upper()),
            (ICO, ICO.upper()),
            (CMAP, CMAP.upper()),
            (ISMAP, ISMAP.upper()),
            (IMAP, IMAP.upper()),
            (CMAPX, CMAPX.upper()),
            (IMAGE_NP, IMAGE_NP.upper()),
            (CMAPX_NP, CMAPX_NP.upper()),
            (JPG, JPG.upper()),
            (JPEG, JPEG.upper()),
            (JPE, JPE.upper()),
            (JPEG_2000, JPEG_2000.upper()),
            (JSON, JSON.upper()),
            (JSON0, JSON0.upper()),
            (DOT_JSON, DOT_JSON.upper()),
            (XDOT_JSON, XDOT_JSON.upper()),
            (PDF, PDF.upper()),
            (PIC, PIC.upper()),
            (PICT, PICT.upper()),
            (APPLE_PICT, APPLE_PICT.upper()),
            (PLAIN_TEXT, PLAIN_TEXT.upper()),
            (PLAIN_EXT, PLAIN_EXT.upper()),
            (PNG, PNG.upper()),
            (POV_RAY, POV_RAY.upper()),
            (PS_PDF, PS_PDF.upper()),
            (PSD, PSD.upper()),
            (SGI, SGI.upper()),
            (SVG, SVG.upper()),
            (SVGZ, SVGZ.upper()),
            (TGA, TGA.upper()),
            (TIF, TIF.upper()),
            (TIFF, TIFF.upper()),
            (TK, TK.upper()),
            (VML, VML.upper()),
            (VMLZ, VMLZ.upper()),
            (VRML, VRML.upper()),
            (WBMP, WBMP.upper()),
            (WEBP, WEBP.upper()),
            (XLIB, XLIB.upper()),
            (X11, X11.upper()),
        ]
        output_format = models.CharField(
            _("Visualization File Output Format"),
            max_length=10,
            choices=FORMAT_CHOICES,
            default=GV,
        )
        graph_source = models.TextField(blank=True, null=True)
        output_file = models.FileField(
            upload_to=settings.MIGRATION_SNAPSHOT_DIR, blank=True, null=True
        )
        created_at = models.DateField(auto_now_add=True)
        modified_at = models.DateField(auto_now=True)

        def __str__(self):
            return f"Snapshot #:{self.pk}"

        def record_snapshot(self):
            graph_name = settings.MIGRATION_SNAPSHOT_FILENAME
            if self.output_format is None:
                self.output_format = settings.DEFAULT_SNAPSHOT_FORMAT

            file_name = f"{graph_name}.{self.output_format}"
            date_end = getattr(self, "_date_end", None)

            try:
                visualizer = MigrationHistoryUtil(
                    output_format=self.output_format, date_end=parse(date_end)
                )
                visualizer.create_snapshot()
                self.graph_source = str(visualizer.source)
                with open(file_name, "rb") as f:
                    self.output_file.save(file_name, File(f))
            finally:
                os.remove(graph_name)
                os.remove(file_name)

    @receiver(post_save, sender=MigrationSnapshot)
    def record_snapshot_signal(sender, instance, **kwargs):
        post_save.disconnect(record_snapshot_signal, sender=MigrationSnapshot)
        instance.record_snapshot()
        post_save.connect(record_snapshot_signal, sender=MigrationSnapshot)
