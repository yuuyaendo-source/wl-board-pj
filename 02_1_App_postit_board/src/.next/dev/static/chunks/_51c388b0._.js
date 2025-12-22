(globalThis.TURBOPACK || (globalThis.TURBOPACK = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/app/board/[id]/page.module.css [app-client] (css module)", ((__turbopack_context__) => {

__turbopack_context__.v({
  "boardContainer": "page-module__9vVkKq__boardContainer",
  "canvasWrapper": "page-module__9vVkKq__canvasWrapper",
  "header": "page-module__9vVkKq__header",
  "status": "page-module__9vVkKq__status",
  "titleInput": "page-module__9vVkKq__titleInput",
});
}),
"[project]/components/BoardCanvas.module.css [app-client] (css module)", ((__turbopack_context__) => {

__turbopack_context__.v({
  "canvas": "BoardCanvas-module__qpzOaa__canvas",
  "svgLayer": "BoardCanvas-module__qpzOaa__svgLayer",
});
}),
"[project]/components/StickyNote.module.css [app-client] (css module)", ((__turbopack_context__) => {

__turbopack_context__.v({
  "colorButton": "StickyNote-module__0cAv8W__colorButton",
  "colorOption": "StickyNote-module__0cAv8W__colorOption",
  "colorPicker": "StickyNote-module__0cAv8W__colorPicker",
  "note": "StickyNote-module__0cAv8W__note",
  "pinButton": "StickyNote-module__0cAv8W__pinButton",
  "pinned": "StickyNote-module__0cAv8W__pinned",
  "textarea": "StickyNote-module__0cAv8W__textarea",
});
}),
"[project]/components/StickyNote.js [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>StickyNote
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__ = __turbopack_context__.i("[project]/components/StickyNote.module.css [app-client] (css module)");
;
var _s = __turbopack_context__.k.signature();
;
;
const COLORS = [
    "#ffeb3b",
    "#a7ffeb",
    "#ffcdd2",
    "#e1bee7",
    "#fff9c4",
    "#c5e1a5",
    "#ffccbc",
    "#b3e5fc",
    "#ffffff"
];
function StickyNote({ note, onUpdate, scale, onMouseDown, onMouseUp }) {
    _s();
    const [isDragging, setIsDragging] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const noteRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const offset = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])({
        x: 0,
        y: 0
    });
    const handleMouseDown = (e)=>{
        if (onMouseDown) onMouseDown(e); // Propagate to parent for line drawing
        if (e.defaultPrevented || e.altKey) return; // Don't drag if line drawing
        if (note.pinned) return; // Don't drag if pinned
        if (e.target.tagName === "TEXTAREA") return; // Allow text selection
        setIsDragging(true);
        const rect = noteRef.current.getBoundingClientRect();
        offset.current = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    };
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "StickyNote.useEffect": ()=>{
            const handleMouseMove = {
                "StickyNote.useEffect.handleMouseMove": (e)=>{
                    if (!isDragging) return;
                    // Calculate new position relative to parent (canvas)
                    // We need to account for scale
                    const parentRect = noteRef.current.parentElement.getBoundingClientRect();
                    const newX = (e.clientX - parentRect.left - offset.current.x) / scale;
                    const newY = (e.clientY - parentRect.top - offset.current.y) / scale;
                    onUpdate({
                        ...note,
                        x: newX,
                        y: newY
                    });
                }
            }["StickyNote.useEffect.handleMouseMove"];
            const handleMouseUp = {
                "StickyNote.useEffect.handleMouseUp": ()=>{
                    setIsDragging(false);
                }
            }["StickyNote.useEffect.handleMouseUp"];
            if (isDragging) {
                window.addEventListener("mousemove", handleMouseMove);
                window.addEventListener("mouseup", handleMouseUp);
            }
            return ({
                "StickyNote.useEffect": ()=>{
                    window.removeEventListener("mousemove", handleMouseMove);
                    window.removeEventListener("mouseup", handleMouseUp);
                }
            })["StickyNote.useEffect"];
        }
    }["StickyNote.useEffect"], [
        isDragging,
        note,
        onUpdate,
        scale
    ]);
    const togglePin = ()=>{
        onUpdate({
            ...note,
            pinned: !note.pinned
        });
    };
    const [showColorPicker, setShowColorPicker] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const changeColor = (newColor)=>{
        onUpdate({
            ...note,
            color: newColor
        });
        setShowColorPicker(false);
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        ref: noteRef,
        className: `${__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].note} ${note.pinned ? __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].pinned : ''}`,
        style: {
            left: note.x,
            top: note.y,
            backgroundColor: note.color,
            transform: `scale(${isDragging ? 1.05 : 1})`,
            zIndex: isDragging ? 1000 : 1
        },
        onMouseDown: handleMouseDown,
        onMouseUp: onMouseUp,
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].pinButton,
                onClick: togglePin,
                title: note.pinned ? "ピン留めを外す" : "ピン留めする",
                children: note.pinned ? "📌" : "📍"
            }, void 0, false, {
                fileName: "[project]/components/StickyNote.js",
                lineNumber: 82,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].colorButton,
                onClick: ()=>setShowColorPicker(!showColorPicker),
                title: "色を変更",
                children: "🎨"
            }, void 0, false, {
                fileName: "[project]/components/StickyNote.js",
                lineNumber: 89,
                columnNumber: 13
            }, this),
            showColorPicker && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].colorPicker,
                children: COLORS.map((c)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].colorOption,
                        style: {
                            backgroundColor: c
                        },
                        onClick: ()=>changeColor(c)
                    }, c, false, {
                        fileName: "[project]/components/StickyNote.js",
                        lineNumber: 99,
                        columnNumber: 25
                    }, this))
            }, void 0, false, {
                fileName: "[project]/components/StickyNote.js",
                lineNumber: 97,
                columnNumber: 17
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("textarea", {
                value: note.text,
                onChange: (e)=>onUpdate({
                        ...note,
                        text: e.target.value
                    }),
                placeholder: "Type here...",
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].textarea
            }, void 0, false, {
                fileName: "[project]/components/StickyNote.js",
                lineNumber: 108,
                columnNumber: 13
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/StickyNote.js",
        lineNumber: 69,
        columnNumber: 9
    }, this);
}
_s(StickyNote, "v4qi7RfHAHENwRkOGnoNjgoJ7yk=");
_c = StickyNote;
var _c;
__turbopack_context__.k.register(_c, "StickyNote");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/BoardCanvas.js [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>BoardCanvas
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$BoardCanvas$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__ = __turbopack_context__.i("[project]/components/BoardCanvas.module.css [app-client] (css module)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$StickyNote$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/StickyNote.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
;
;
;
function BoardCanvas({ notes, lines, onUpdateNote, onAddLine, scale }) {
    _s();
    const [drawingLine, setDrawingLine] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null); // { startNoteId, startX, startY, currentX, currentY }
    // Handle line drawing logic here if needed, or keep it simple for now
    // For MVP, we'll just render notes and lines
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$BoardCanvas$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].canvas,
        style: {
            transform: `scale(${scale})`,
            transformOrigin: "0 0",
            width: "100%",
            height: "100%"
        },
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$BoardCanvas$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].svgLayer,
                children: lines.map((line, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("line", {
                        x1: line.x1,
                        y1: line.y1,
                        x2: line.x2,
                        y2: line.y2,
                        stroke: "#333",
                        strokeWidth: "2"
                    }, i, false, {
                        fileName: "[project]/components/BoardCanvas.js",
                        lineNumber: 23,
                        columnNumber: 21
                    }, this))
            }, void 0, false, {
                fileName: "[project]/components/BoardCanvas.js",
                lineNumber: 21,
                columnNumber: 13
            }, this),
            notes.map((note)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$StickyNote$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                    note: note,
                    onUpdate: onUpdateNote,
                    scale: scale
                }, note.id, false, {
                    fileName: "[project]/components/BoardCanvas.js",
                    lineNumber: 36,
                    columnNumber: 17
                }, this))
        ]
    }, void 0, true, {
        fileName: "[project]/components/BoardCanvas.js",
        lineNumber: 12,
        columnNumber: 9
    }, this);
}
_s(BoardCanvas, "zEI/RpfsL6utmlhjF5svV0Ts0/k=");
_c = BoardCanvas;
var _c;
__turbopack_context__.k.register(_c, "BoardCanvas");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/Toolbar.module.css [app-client] (css module)", ((__turbopack_context__) => {

__turbopack_context__.v({
  "active": "Toolbar-module__VaI4xq__active",
  "addButton": "Toolbar-module__VaI4xq__addButton",
  "colorBtn": "Toolbar-module__VaI4xq__colorBtn",
  "divider": "Toolbar-module__VaI4xq__divider",
  "group": "Toolbar-module__VaI4xq__group",
  "toolbar": "Toolbar-module__VaI4xq__toolbar",
});
}),
"[project]/components/Toolbar.js [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>Toolbar
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__ = __turbopack_context__.i("[project]/components/Toolbar.module.css [app-client] (css module)");
;
var _s = __turbopack_context__.k.signature();
;
;
const COLORS = [
    "#ffeb3b",
    "#a7ffeb",
    "#ffcdd2",
    "#e1bee7",
    "#fff9c4",
    "#c5e1a5",
    "#ffccbc",
    "#b3e5fc",
    "#ffffff" // White
];
function Toolbar({ onAddNote, color, setColor, scale, setScale, onDownload, onUpload }) {
    _s();
    const fileInputRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const handleFileUpload = (e)=>{
        const file = e.target.files?.[0];
        if (file) {
            onUpload(file);
            e.target.value = ''; // Reset input
        }
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].toolbar,
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].group,
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                    onClick: onAddNote,
                    className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].addButton,
                    children: "+ 付箋"
                }, void 0, false, {
                    fileName: "[project]/components/Toolbar.js",
                    lineNumber: 30,
                    columnNumber: 17
                }, this)
            }, void 0, false, {
                fileName: "[project]/components/Toolbar.js",
                lineNumber: 29,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].divider
            }, void 0, false, {
                fileName: "[project]/components/Toolbar.js",
                lineNumber: 35,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].group,
                children: COLORS.map((c)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        className: `${__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].colorBtn} ${color === c ? __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].active : ""}`,
                        style: {
                            backgroundColor: c
                        },
                        onClick: ()=>setColor(c)
                    }, c, false, {
                        fileName: "[project]/components/Toolbar.js",
                        lineNumber: 39,
                        columnNumber: 21
                    }, this))
            }, void 0, false, {
                fileName: "[project]/components/Toolbar.js",
                lineNumber: 37,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].divider
            }, void 0, false, {
                fileName: "[project]/components/Toolbar.js",
                lineNumber: 48,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].group,
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        onClick: ()=>setScale((s)=>Math.max(0.5, s - 0.1)),
                        children: "-"
                    }, void 0, false, {
                        fileName: "[project]/components/Toolbar.js",
                        lineNumber: 51,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        children: [
                            Math.round(scale * 100),
                            "%"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/Toolbar.js",
                        lineNumber: 52,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        onClick: ()=>setScale((s)=>Math.min(2, s + 0.1)),
                        children: "+"
                    }, void 0, false, {
                        fileName: "[project]/components/Toolbar.js",
                        lineNumber: 53,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/Toolbar.js",
                lineNumber: 50,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].divider
            }, void 0, false, {
                fileName: "[project]/components/Toolbar.js",
                lineNumber: 56,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].group,
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        onClick: onDownload,
                        title: "ボードをダウンロード",
                        children: "💾"
                    }, void 0, false, {
                        fileName: "[project]/components/Toolbar.js",
                        lineNumber: 59,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                        type: "file",
                        accept: ".json",
                        onChange: handleFileUpload,
                        style: {
                            display: 'none'
                        },
                        ref: (ref)=>{
                            if (fileInputRef) fileInputRef.current = ref;
                        }
                    }, void 0, false, {
                        fileName: "[project]/components/Toolbar.js",
                        lineNumber: 60,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        onClick: ()=>document.querySelector('input[type="file"]')?.click(),
                        title: "ボードをアップロード",
                        children: "📂"
                    }, void 0, false, {
                        fileName: "[project]/components/Toolbar.js",
                        lineNumber: 67,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/Toolbar.js",
                lineNumber: 58,
                columnNumber: 13
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/Toolbar.js",
        lineNumber: 28,
        columnNumber: 9
    }, this);
}
_s(Toolbar, "YQqvMxdmg33cmOXmQcOjJm+FLVI=");
_c = Toolbar;
var _c;
__turbopack_context__.k.register(_c, "Toolbar");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/app/board/[id]/page.js [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>BoardPage
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/navigation.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$socket$2e$io$2d$client$2f$build$2f$esm$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/node_modules/socket.io-client/build/esm/index.js [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$app$2f$board$2f5b$id$5d2f$page$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__ = __turbopack_context__.i("[project]/app/board/[id]/page.module.css [app-client] (css module)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$BoardCanvas$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/BoardCanvas.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/Toolbar.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
;
;
;
let socket;
function BoardPage() {
    _s();
    const { id: boardId } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useParams"])();
    const [notes, setNotes] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [lines, setLines] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [color, setColor] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("#ffeb3b"); // Default yellow
    const [isConnected, setIsConnected] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [scale, setScale] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(1);
    const [title, setTitle] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("");
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "BoardPage.useEffect": ()=>{
            // Initialize Socket.io connection with reconnection options
            socket = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$socket$2e$io$2d$client$2f$build$2f$esm$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["default"])({
                reconnection: true,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 5000,
                reconnectionAttempts: Infinity
            });
            socket.on("connect", {
                "BoardPage.useEffect": ()=>{
                    console.log("Connected to server");
                    setIsConnected(true);
                    socket.emit("join-board", boardId);
                }
            }["BoardPage.useEffect"]);
            socket.on("init-board", {
                "BoardPage.useEffect": (data)=>{
                    setNotes(data.notes || []);
                    setLines(data.lines || []);
                }
            }["BoardPage.useEffect"]);
            socket.on("note-added", {
                "BoardPage.useEffect": (note)=>{
                    setNotes({
                        "BoardPage.useEffect": (prev)=>{
                            // Prevent duplicate - check if note with this ID already exists
                            if (prev.some({
                                "BoardPage.useEffect": (n)=>n.id === note.id
                            }["BoardPage.useEffect"])) {
                                return prev;
                            }
                            return [
                                ...prev,
                                note
                            ];
                        }
                    }["BoardPage.useEffect"]);
                }
            }["BoardPage.useEffect"]);
            socket.on("note-updated", {
                "BoardPage.useEffect": (updatedNote)=>{
                    setNotes({
                        "BoardPage.useEffect": (prev)=>prev.map({
                                "BoardPage.useEffect": (n)=>n.id === updatedNote.id ? updatedNote : n
                            }["BoardPage.useEffect"])
                    }["BoardPage.useEffect"]);
                }
            }["BoardPage.useEffect"]);
            socket.on("line-added", {
                "BoardPage.useEffect": (line)=>{
                    setLines({
                        "BoardPage.useEffect": (prev)=>[
                                ...prev,
                                line
                            ]
                    }["BoardPage.useEffect"]);
                }
            }["BoardPage.useEffect"]);
            socket.on("disconnect", {
                "BoardPage.useEffect": ()=>{
                    console.log("Disconnected from server");
                    setIsConnected(false);
                }
            }["BoardPage.useEffect"]);
            return ({
                "BoardPage.useEffect": ()=>{
                    socket.disconnect();
                }
            })["BoardPage.useEffect"];
        }
    }["BoardPage.useEffect"], [
        boardId
    ]);
    const addNote = ()=>{
        // Generate more unique ID with timestamp + random
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substr(2, 9);
        // Position new notes at bottom center of viewport
        const container = document.querySelector(`.${__TURBOPACK__imported__module__$5b$project$5d2f$app$2f$board$2f5b$id$5d2f$page$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].boardContainer}`);
        const containerRect = container?.getBoundingClientRect() || {
            width: window.innerWidth,
            height: window.innerHeight
        };
        const scrollLeft = container?.scrollLeft || 0;
        const scrollTop = container?.scrollTop || 0;
        const centerX = scrollLeft + containerRect.width / 2 - 100; // Center minus half note width
        const bottomY = scrollTop + containerRect.height - 280; // Bottom minus note height and some margin
        const newNote = {
            id: `${timestamp}-${random}`,
            text: "",
            x: centerX + Math.random() * 20 - 10,
            y: bottomY + Math.random() * 20 - 10,
            color: color,
            pinned: false
        };
        // Optimistic update
        setNotes((prev)=>[
                ...prev,
                newNote
            ]);
        socket.emit("add-note", {
            boardId,
            note: newNote
        });
    };
    const updateTimeout = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const updateNote = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "BoardPage.useCallback[updateNote]": (updatedNote)=>{
            setNotes({
                "BoardPage.useCallback[updateNote]": (prev)=>prev.map({
                        "BoardPage.useCallback[updateNote]": (n)=>n.id === updatedNote.id ? updatedNote : n
                    }["BoardPage.useCallback[updateNote]"])
            }["BoardPage.useCallback[updateNote]"]);
            // Debounce: only send to server after 100ms of no updates
            if (updateTimeout.current) {
                clearTimeout(updateTimeout.current);
            }
            updateTimeout.current = setTimeout({
                "BoardPage.useCallback[updateNote]": ()=>{
                    socket.emit("update-note", {
                        boardId,
                        note: updatedNote
                    });
                }
            }["BoardPage.useCallback[updateNote]"], 100);
        }
    }["BoardPage.useCallback[updateNote]"], [
        boardId
    ]);
    const addLine = (line)=>{
        setLines((prev)=>[
                ...prev,
                line
            ]);
        socket.emit("add-line", {
            boardId,
            line
        });
    };
    const handleDownload = ()=>{
        const boardData = {
            id: boardId,
            title,
            notes,
            lines,
            exportedAt: new Date().toISOString()
        };
        const dataStr = JSON.stringify(boardData, null, 2);
        const dataBlob = new Blob([
            dataStr
        ], {
            type: 'application/json'
        });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `board-${boardId}-${Date.now()}.json`;
        link.click();
        URL.revokeObjectURL(url);
    };
    const handleUpload = (file)=>{
        const reader = new FileReader();
        reader.onload = (e)=>{
            try {
                const boardData = JSON.parse(e.target.result);
                if (boardData.title) setTitle(boardData.title);
                if (boardData.notes) setNotes(boardData.notes);
                if (boardData.lines) setLines(boardData.lines);
                // Emit to server to sync with other clients
                boardData.notes?.forEach((note)=>{
                    socket.emit("add-note", {
                        boardId,
                        note
                    });
                });
                alert('ボードを復元しました!');
            } catch (error) {
                console.error('Error parsing board data:', error);
                alert('ファイルの読み込みに失敗しました。');
            }
        };
        reader.readAsText(file);
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: __TURBOPACK__imported__module__$5b$project$5d2f$app$2f$board$2f5b$id$5d2f$page$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].boardContainer,
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$app$2f$board$2f5b$id$5d2f$page$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].header,
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                        type: "text",
                        value: title,
                        onChange: (e)=>setTitle(e.target.value),
                        placeholder: "ボードタイトルを入力...",
                        className: __TURBOPACK__imported__module__$5b$project$5d2f$app$2f$board$2f5b$id$5d2f$page$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].titleInput
                    }, void 0, false, {
                        fileName: "[project]/app/board/[id]/page.js",
                        lineNumber: 168,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: __TURBOPACK__imported__module__$5b$project$5d2f$app$2f$board$2f5b$id$5d2f$page$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].status,
                        children: isConnected ? "🟢 Online" : "🔴 Offline"
                    }, void 0, false, {
                        fileName: "[project]/app/board/[id]/page.js",
                        lineNumber: 175,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/app/board/[id]/page.js",
                lineNumber: 167,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                onAddNote: addNote,
                color: color,
                setColor: setColor,
                scale: scale,
                setScale: setScale,
                onDownload: handleDownload,
                onUpload: handleUpload
            }, void 0, false, {
                fileName: "[project]/app/board/[id]/page.js",
                lineNumber: 180,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$app$2f$board$2f5b$id$5d2f$page$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].canvasWrapper,
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$BoardCanvas$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                    notes: notes,
                    lines: lines,
                    onUpdateNote: updateNote,
                    onAddLine: addLine,
                    scale: scale
                }, void 0, false, {
                    fileName: "[project]/app/board/[id]/page.js",
                    lineNumber: 191,
                    columnNumber: 17
                }, this)
            }, void 0, false, {
                fileName: "[project]/app/board/[id]/page.js",
                lineNumber: 190,
                columnNumber: 13
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/app/board/[id]/page.js",
        lineNumber: 166,
        columnNumber: 9
    }, this);
}
_s(BoardPage, "hqZTPXaD3ZqX020I1TAQf7CKo/w=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useParams"]
    ];
});
_c = BoardPage;
var _c;
__turbopack_context__.k.register(_c, "BoardPage");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
]);

//# sourceMappingURL=_51c388b0._.js.map