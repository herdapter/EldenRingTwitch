import express from 'express';
import multer from 'multer';
import fs from 'fs';
import { parse_save_internal_rust } from './elden-ring-save-parser/elden_ring_save_parser.js';

const app = express();
const upload = multer({ dest: '/tmp/' });

app.use(express.json());

app.post('/parse', upload.single('save_file'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ success: false, error: 'No file uploaded' });
        }

        const saveData = fs.readFileSync(req.file.path);
        const save = new Uint8Array(saveData);

        const result = parse_save_internal_rust(save);

        // Cleanup temp file
        fs.unlinkSync(req.file.path);

        // Convert BigInt to string for JSON
        const jsonResult = JSON.parse(JSON.stringify(result, (key, value) =>
            typeof value === 'bigint' ? value.toString() : value
        ));

        res.json({
            success: true,
            data: jsonResult
        });

    } catch (error) {
        console.error('Parse error:', error);

        // Cleanup on error
        if (req.file && fs.existsSync(req.file.path)) {
            fs.unlinkSync(req.file.path);
        }

        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`🎮 Elden Ring Parser service running on port ${PORT}`);
});