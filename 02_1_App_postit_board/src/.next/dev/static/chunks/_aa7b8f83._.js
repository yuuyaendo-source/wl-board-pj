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
  "groupBadge": "StickyNote-module__0cAv8W__groupBadge",
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
        e.stopPropagation(); // Prevent board scroll when dragging note
        e.preventDefault(); // Also prevent default to ensure board drag doesn't start
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
        "data-sticky-note": "true",
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
                lineNumber: 87,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].colorButton,
                onClick: ()=>setShowColorPicker(!showColorPicker),
                title: "色を変更",
                children: "🎨"
            }, void 0, false, {
                fileName: "[project]/components/StickyNote.js",
                lineNumber: 94,
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
                        lineNumber: 104,
                        columnNumber: 25
                    }, this))
            }, void 0, false, {
                fileName: "[project]/components/StickyNote.js",
                lineNumber: 102,
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
                lineNumber: 113,
                columnNumber: 13
            }, this),
            note.groupId && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].groupBadge,
                title: `Group ID: ${note.groupId}`,
                children: "🔗 Group"
            }, void 0, false, {
                fileName: "[project]/components/StickyNote.js",
                lineNumber: 120,
                columnNumber: 17
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/StickyNote.js",
        lineNumber: 73,
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
            width: "4000px",
            height: "4000px"
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
function Toolbar({ onAddNote, color, setColor, scale, setScale, onDownload, onUpload, onToggleCommentPanel, onCenter }) {
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
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].divider
            }, void 0, false, {
                fileName: "[project]/components/Toolbar.js",
                lineNumber: 70,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].group,
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                    onClick: onCenter,
                    title: "中央に戻る",
                    children: "🎯"
                }, void 0, false, {
                    fileName: "[project]/components/Toolbar.js",
                    lineNumber: 73,
                    columnNumber: 17
                }, this)
            }, void 0, false, {
                fileName: "[project]/components/Toolbar.js",
                lineNumber: 72,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].divider
            }, void 0, false, {
                fileName: "[project]/components/Toolbar.js",
                lineNumber: 76,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].group,
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                    onClick: onToggleCommentPanel,
                    title: "コメント一覧",
                    children: "📝"
                }, void 0, false, {
                    fileName: "[project]/components/Toolbar.js",
                    lineNumber: 79,
                    columnNumber: 17
                }, this)
            }, void 0, false, {
                fileName: "[project]/components/Toolbar.js",
                lineNumber: 78,
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
"[project]/components/CommentListPanel.module.css [app-client] (css module)", ((__turbopack_context__) => {

__turbopack_context__.v({
  "actionButtons": "CommentListPanel-module__9DGtxq__actionButtons",
  "actions": "CommentListPanel-module__9DGtxq__actions",
  "checkbox": "CommentListPanel-module__9DGtxq__checkbox",
  "closeButton": "CommentListPanel-module__9DGtxq__closeButton",
  "groupBadge": "CommentListPanel-module__9DGtxq__groupBadge",
  "groupButton": "CommentListPanel-module__9DGtxq__groupButton",
  "header": "CommentListPanel-module__9DGtxq__header",
  "noteItem": "CommentListPanel-module__9DGtxq__noteItem",
  "noteList": "CommentListPanel-module__9DGtxq__noteList",
  "notePreview": "CommentListPanel-module__9DGtxq__notePreview",
  "noteText": "CommentListPanel-module__9DGtxq__noteText",
  "panel": "CommentListPanel-module__9DGtxq__panel",
  "pinnedBadge": "CommentListPanel-module__9DGtxq__pinnedBadge",
  "selected": "CommentListPanel-module__9DGtxq__selected",
  "ungroupButton": "CommentListPanel-module__9DGtxq__ungroupButton",
});
}),
"[project]/components/CommentListPanel.js [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>CommentListPanel
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__ = __turbopack_context__.i("[project]/components/CommentListPanel.module.css [app-client] (css module)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
function CommentListPanel({ notes, onJumpToNote, onGroupNotes, onUngroupNotes, onClose }) {
    _s();
    const [selectedNotes, setSelectedNotes] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const toggleSelection = (noteId)=>{
        if (selectedNotes.includes(noteId)) {
            setSelectedNotes(selectedNotes.filter((id)=>id !== noteId));
        } else {
            setSelectedNotes([
                ...selectedNotes,
                noteId
            ]);
        }
    };
    const handleGroupSelected = ()=>{
        if (selectedNotes.length < 2) {
            alert("グループ化するには2つ以上の付箋を選択してください");
            return;
        }
        onGroupNotes(selectedNotes);
        setSelectedNotes([]);
    };
    const handleUngroupSelected = ()=>{
        if (selectedNotes.length === 0) {
            alert("解除する付箋を選択してください");
            return;
        }
        onUngroupNotes(selectedNotes);
        setSelectedNotes([]);
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].panel,
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].header,
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                        children: "コメント一覧"
                    }, void 0, false, {
                        fileName: "[project]/components/CommentListPanel.js",
                        lineNumber: 38,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        onClick: onClose,
                        className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].closeButton,
                        children: "✕"
                    }, void 0, false, {
                        fileName: "[project]/components/CommentListPanel.js",
                        lineNumber: 39,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/CommentListPanel.js",
                lineNumber: 37,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].actions,
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        children: [
                            selectedNotes.length,
                            " 個選択中"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/CommentListPanel.js",
                        lineNumber: 43,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].actionButtons,
                        children: [
                            selectedNotes.length >= 2 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: handleGroupSelected,
                                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].groupButton,
                                children: "グループ化"
                            }, void 0, false, {
                                fileName: "[project]/components/CommentListPanel.js",
                                lineNumber: 46,
                                columnNumber: 25
                            }, this),
                            selectedNotes.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: handleUngroupSelected,
                                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].ungroupButton,
                                children: "解除"
                            }, void 0, false, {
                                fileName: "[project]/components/CommentListPanel.js",
                                lineNumber: 51,
                                columnNumber: 25
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/CommentListPanel.js",
                        lineNumber: 44,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/CommentListPanel.js",
                lineNumber: 42,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].noteList,
                children: notes.map((note)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: `${__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].noteItem} ${selectedNotes.includes(note.id) ? __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].selected : ''}`,
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                type: "checkbox",
                                checked: selectedNotes.includes(note.id),
                                onChange: ()=>toggleSelection(note.id),
                                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].checkbox
                            }, void 0, false, {
                                fileName: "[project]/components/CommentListPanel.js",
                                lineNumber: 64,
                                columnNumber: 25
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].notePreview,
                                style: {
                                    backgroundColor: note.color
                                },
                                onClick: ()=>onJumpToNote(note),
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].noteText,
                                        children: note.text || "(空白)"
                                    }, void 0, false, {
                                        fileName: "[project]/components/CommentListPanel.js",
                                        lineNumber: 75,
                                        columnNumber: 29
                                    }, this),
                                    note.pinned && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].pinnedBadge,
                                        children: "📌"
                                    }, void 0, false, {
                                        fileName: "[project]/components/CommentListPanel.js",
                                        lineNumber: 78,
                                        columnNumber: 45
                                    }, this),
                                    note.groupId && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].groupBadge,
                                        children: [
                                            "Group ",
                                            note.groupId
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/CommentListPanel.js",
                                        lineNumber: 79,
                                        columnNumber: 46
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/CommentListPanel.js",
                                lineNumber: 70,
                                columnNumber: 25
                            }, this)
                        ]
                    }, note.id, true, {
                        fileName: "[project]/components/CommentListPanel.js",
                        lineNumber: 60,
                        columnNumber: 21
                    }, this))
            }, void 0, false, {
                fileName: "[project]/components/CommentListPanel.js",
                lineNumber: 58,
                columnNumber: 13
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/CommentListPanel.js",
        lineNumber: 36,
        columnNumber: 9
    }, this);
}
_s(CommentListPanel, "eXeqd/Vj6KQK9bs+U0ZzFfuJH7Y=");
_c = CommentListPanel;
var _c;
__turbopack_context__.k.register(_c, "CommentListPanel");
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
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/CommentListPanel.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
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
    const [showCommentPanel, setShowCommentPanel] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const boardContainerRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
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
    // Scroll to center on initial load
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "BoardPage.useEffect": ()=>{
            const container = boardContainerRef.current;
            if (container) {
                // Wait a bit for layout
                setTimeout({
                    "BoardPage.useEffect": ()=>{
                        const scrollX = (4000 - container.clientWidth) / 2;
                        const scrollY = (4000 - container.clientHeight) / 2;
                        container.scrollTo(scrollX, scrollY);
                    }
                }["BoardPage.useEffect"], 100);
            }
        }
    }["BoardPage.useEffect"], []);
    const handleCenter = ()=>{
        const container = boardContainerRef.current;
        if (container) {
            const scrollX = (4000 - container.clientWidth) / 2;
            const scrollY = (4000 - container.clientHeight) / 2;
            container.scrollTo({
                left: scrollX,
                top: scrollY,
                behavior: 'smooth'
            });
        }
    };
    const addNote = ()=>{
        // Generate more unique ID with timestamp + random
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substr(2, 9);
        // Position new notes near the bottom center of the CURRENT VIEWPORT
        const container = boardContainerRef.current;
        if (!container) return;
        const viewportWidth = container.clientWidth;
        const viewportHeight = container.clientHeight;
        const scrollLeft = container.scrollLeft;
        const scrollTop = container.scrollTop;
        // Calculate center x relative to the board
        const centerX = scrollLeft + viewportWidth / 2 - 100; // Center minus half note width
        // Calculate bottom y relative to the board (near toolbar)
        // Toolbar is at bottom 20px + padding ~50px. Let's place it 200px from bottom.
        const bottomY = scrollTop + viewportHeight - 300;
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
    const notesRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(notes);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "BoardPage.useEffect": ()=>{
            notesRef.current = notes;
        }
    }["BoardPage.useEffect"], [
        notes
    ]);
    const updateTimeout = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const updateNote = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "BoardPage.useCallback[updateNote]": (updatedNote)=>{
            const currentNotes = notesRef.current;
            const originalNote = currentNotes.find({
                "BoardPage.useCallback[updateNote].originalNote": (n)=>n.id === updatedNote.id
            }["BoardPage.useCallback[updateNote].originalNote"]);
            let notesToUpdate = [
                updatedNote
            ];
            if (originalNote && updatedNote.groupId) {
                const dx = updatedNote.x - originalNote.x;
                const dy = updatedNote.y - originalNote.y;
                if (dx !== 0 || dy !== 0) {
                    const groupNotes = currentNotes.filter({
                        "BoardPage.useCallback[updateNote].groupNotes": (n)=>n.groupId === updatedNote.groupId && n.id !== updatedNote.id
                    }["BoardPage.useCallback[updateNote].groupNotes"]);
                    const additionalUpdates = groupNotes.map({
                        "BoardPage.useCallback[updateNote].additionalUpdates": (n)=>({
                                ...n,
                                x: n.x + dx,
                                y: n.y + dy
                            })
                    }["BoardPage.useCallback[updateNote].additionalUpdates"]);
                    notesToUpdate = [
                        ...notesToUpdate,
                        ...additionalUpdates
                    ];
                }
            }
            setNotes({
                "BoardPage.useCallback[updateNote]": (prev)=>{
                    return prev.map({
                        "BoardPage.useCallback[updateNote]": (n)=>{
                            const updated = notesToUpdate.find({
                                "BoardPage.useCallback[updateNote].updated": (un)=>un.id === n.id
                            }["BoardPage.useCallback[updateNote].updated"]);
                            return updated || n;
                        }
                    }["BoardPage.useCallback[updateNote]"]);
                }
            }["BoardPage.useCallback[updateNote]"]);
            // Debounce: only send to server after 100ms of no updates
            if (updateTimeout.current) {
                clearTimeout(updateTimeout.current);
            }
            updateTimeout.current = setTimeout({
                "BoardPage.useCallback[updateNote]": ()=>{
                    notesToUpdate.forEach({
                        "BoardPage.useCallback[updateNote]": (note)=>{
                            socket.emit("update-note", {
                                boardId,
                                note
                            });
                        }
                    }["BoardPage.useCallback[updateNote]"]);
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
    const handleJumpToNote = (note)=>{
        const container = boardContainerRef.current;
        if (container) {
            // Calculate scroll position to center the note
            const noteX = note.x * scale;
            const noteY = note.y * scale;
            const centerX = noteX - container.clientWidth / 2 + 100;
            const centerY = noteY - container.clientHeight / 2 + 100;
            container.scrollTo({
                left: Math.max(0, centerX),
                top: Math.max(0, centerY),
                behavior: 'smooth'
            });
            // Highlight effect
            setTimeout(()=>{
                const noteElement = document.querySelector(`[data-note-id="${note.id}"]`);
                if (noteElement) {
                    noteElement.style.animation = 'highlight 1s';
                    setTimeout(()=>noteElement.style.animation = '', 1000);
                }
            }, 500);
        }
    };
    const handleGroupNotes = (noteIds)=>{
        const groupId = `group-${Date.now()}`;
        // Calculate center position from selected notes
        const selectedNotes = notes.filter((n)=>noteIds.includes(n.id));
        if (selectedNotes.length === 0) return;
        const centerX = selectedNotes.reduce((sum, n)=>sum + n.x, 0) / selectedNotes.length;
        const centerY = selectedNotes.reduce((sum, n)=>sum + n.y, 0) / selectedNotes.length;
        // Arrange notes in a circle around the center
        const radius = 250;
        const angleStep = 2 * Math.PI / selectedNotes.length;
        const updatedNotes = selectedNotes.map((note, index)=>{
            const angle = angleStep * index;
            const newX = centerX + Math.cos(angle) * radius;
            const newY = centerY + Math.sin(angle) * radius;
            return {
                ...note,
                x: newX,
                y: newY,
                groupId
            };
        });
        setNotes((prev)=>prev.map((n)=>{
                const updated = updatedNotes.find((un)=>un.id === n.id);
                return updated || n;
            }));
        // Update on server
        updatedNotes.forEach((note)=>{
            socket.emit("update-note", {
                boardId,
                note
            });
        });
        alert(`${noteIds.length}個の付箋をグループ化しました`);
    };
    const handleUngroupNotes = (noteIds)=>{
        setNotes((prev)=>prev.map((n)=>noteIds.includes(n.id) ? {
                    ...n,
                    groupId: null
                } : n));
        // Update on server
        noteIds.forEach((noteId)=>{
            const note = notes.find((n)=>n.id === noteId);
            if (note) {
                socket.emit("update-note", {
                    boardId,
                    note: {
                        ...note,
                        groupId: null
                    }
                });
            }
        });
        alert(`${noteIds.length}個の付箋のグループ化を解除しました`);
    };
    const [isDraggingBoard, setIsDraggingBoard] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const dragStart = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])({
        x: 0,
        y: 0
    });
    const scrollStart = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])({
        left: 0,
        top: 0
    });
    const handleMouseDown = (e)=>{
        // Only drag if clicking on the container or canvas directly (not notes)
        // Check if the event target is within a sticky note using data attribute
        const isClickingNote = e.target.closest('[data-sticky-note]');
        if (!isClickingNote) {
            setIsDraggingBoard(true);
            dragStart.current = {
                x: e.clientX,
                y: e.clientY
            };
            const container = boardContainerRef.current;
            scrollStart.current = {
                left: container.scrollLeft,
                top: container.scrollTop
            };
            container.style.cursor = 'grabbing';
        }
    };
    const handleMouseMove = (e)=>{
        if (!isDraggingBoard) return;
        e.preventDefault();
        const container = boardContainerRef.current;
        const dx = e.clientX - dragStart.current.x;
        const dy = e.clientY - dragStart.current.y;
        container.scrollLeft = scrollStart.current.left - dx;
        container.scrollTop = scrollStart.current.top - dy;
    };
    const handleMouseUp = ()=>{
        setIsDraggingBoard(false);
        if (boardContainerRef.current) {
            boardContainerRef.current.style.cursor = 'grab';
        }
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: __TURBOPACK__imported__module__$5b$project$5d2f$app$2f$board$2f5b$id$5d2f$page$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].boardContainer,
        ref: boardContainerRef,
        onMouseDown: handleMouseDown,
        onMouseMove: handleMouseMove,
        onMouseUp: handleMouseUp,
        onMouseLeave: handleMouseUp,
        style: {
            cursor: 'grab'
        },
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
                        lineNumber: 367,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: __TURBOPACK__imported__module__$5b$project$5d2f$app$2f$board$2f5b$id$5d2f$page$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].status,
                        children: isConnected ? "🟢 Online" : "🔴 Offline"
                    }, void 0, false, {
                        fileName: "[project]/app/board/[id]/page.js",
                        lineNumber: 374,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/app/board/[id]/page.js",
                lineNumber: 366,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Toolbar$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                onAddNote: addNote,
                color: color,
                setColor: setColor,
                scale: scale,
                setScale: setScale,
                onDownload: handleDownload,
                onUpload: handleUpload,
                onToggleCommentPanel: ()=>setShowCommentPanel(!showCommentPanel),
                onCenter: handleCenter
            }, void 0, false, {
                fileName: "[project]/app/board/[id]/page.js",
                lineNumber: 379,
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
                    lineNumber: 392,
                    columnNumber: 17
                }, this)
            }, void 0, false, {
                fileName: "[project]/app/board/[id]/page.js",
                lineNumber: 391,
                columnNumber: 13
            }, this),
            showCommentPanel && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$CommentListPanel$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                notes: notes,
                onJumpToNote: handleJumpToNote,
                onGroupNotes: handleGroupNotes,
                onUngroupNotes: handleUngroupNotes,
                onClose: ()=>setShowCommentPanel(false)
            }, void 0, false, {
                fileName: "[project]/app/board/[id]/page.js",
                lineNumber: 402,
                columnNumber: 17
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/app/board/[id]/page.js",
        lineNumber: 357,
        columnNumber: 9
    }, this);
}
_s(BoardPage, "EEO4OhPGsD9lvc9ElXfJDCTcNIA=", false, function() {
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

//# sourceMappingURL=_aa7b8f83._.js.map