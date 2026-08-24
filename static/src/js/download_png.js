/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted } from "@odoo/owl";

class DownloadPngAction extends Component {
    static template = "isd_layout_builder.DownloadPngAction";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");

        onMounted(async () => {
            await this._downloadPng();
        });
    }

    async _downloadPng() {
        const params = this.props.action.params || {};
        const recordId = params.record_id;

        if (!recordId) {
            console.error("isd_layout_builder.download_png: missing record_id param");
            this._goBack();
            return;
        }

        try {
            // Fetch the layout type record
            const records = await this.orm.read(
                "isd.layout.type",
                [recordId],
                ["name", "view_box_width", "view_box_height"]
            );

            if (!records || records.length === 0) {
                console.error("isd_layout_builder.download_png: record not found");
                this._goBack();
                return;
            }

            const record = records[0];
            const vbw = parseFloat(record.view_box_width);
            const vbh = parseFloat(record.view_box_height);
            const recordName = record.name || "layout";

            // Fetch the system frames
            const systems = await this.orm.searchRead(
                "isd.layout.system",
                [["layout_type_id", "=", recordId]],
                ["no", "frame_type", "is_qr", "x", "y", "width", "height"],
                { order: "no asc" }
            );

            // Draw on canvas
            const scale = 5;
            const canvas = document.createElement("canvas");
            canvas.width = vbw * scale;
            canvas.height = vbh * scale;

            const ctx = canvas.getContext("2d");

            // Background
            ctx.fillStyle = "#cccccc";
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Draw each frame
            for (const system of systems) {
                const sx = system.x * scale;
                const sy = system.y * scale;
                const sw = system.width * scale;
                const sh = system.height * scale;

                if (system.is_qr) {
                    // QR frame: white filled rect
                    ctx.fillStyle = "#ffffff";
                    ctx.fillRect(sx, sy, sw, sh);
                } else {
                    // Image frame: clear (transparent)
                    ctx.clearRect(sx, sy, sw, sh);
                }
            }

            // Trigger browser download
            const link = document.createElement("a");
            link.download = `${recordName}.png`;
            link.href = canvas.toDataURL("image/png");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

        } catch (error) {
            console.error("isd_layout_builder.download_png error:", error);
        } finally {
            this._goBack();
        }
    }

    _goBack() {
        if (window.history.length > 1) {
            window.history.back();
        } else {
            this.actionService.doAction({ type: "ir.actions.act_window_close" });
        }
    }
}

registry
    .category("actions")
    .add("isd_layout_builder.download_png", DownloadPngAction);
