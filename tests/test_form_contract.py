from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient

from backend.app.domain.models import ConversionConfig, ConversionResult
from backend.app.main import app


def test_frontend_form_accepts_numeric_quality_scale() -> None:
    def fake_convert(config: ConversionConfig) -> ConversionResult:
        output = Path(config.output_path)
        output.write_bytes(b'%PDF-1.4\n%%EOF')
        return ConversionResult(
            message='ok',
            output_path=str(output),
            output_format='pdf',
            generated_count=1,
            source_label_count=1,
            total_rendered_labels=1,
        )

    async def send_request():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://testserver') as client:
            return await client.post(
                '/api/v1/zpl/convert',
                files={'file': ('shipping.zpl', b'^XA^XZ', 'text/plain')},
                data={
                    'output_format': 'pdf',
                    'width_in': '4',
                    'height_in': '6',
                    'dpmm': '12',
                    'quality_scale': '2',
                    'channels_per_row': '1',
                    'die_cut_enabled': 'true',
                    'die_cut_margin_mm': '5',
                    'die_cut_columns': '2',
                    'png_prefix': 'etiqueta',
                },
            )

    with patch('backend.app.api.routes.zpl.convert_zpl', side_effect=fake_convert):
        response = asyncio.run(send_request())

    assert response.status_code == 200
