(globalThis.TURBOPACK || (globalThis.TURBOPACK = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.module.css [app-client] (css module)", ((__turbopack_context__) => {

__turbopack_context__.v({
  "boardContainer": "page-module__968Xwa__boardContainer",
  "canvasWrapper": "page-module__968Xwa__canvasWrapper",
  "header": "page-module__968Xwa__header",
  "status": "page-module__968Xwa__status",
  "titleInput": "page-module__968Xwa__titleInput",
});
}),
"[project]/02_Projects/02_1_App_brain-storming/src/components/BoardCanvas.module.css [app-client] (css module)", ((__turbopack_context__) => {

__turbopack_context__.v({
  "canvas": "BoardCanvas-module__LAfqOa__canvas",
  "svgLayer": "BoardCanvas-module__LAfqOa__svgLayer",
});
}),
"[project]/02_Projects/02_1_App_brain-storming/src/components/StickyNote.module.css [app-client] (css module)", ((__turbopack_context__) => {

__turbopack_context__.v({
  "authorBadge": "StickyNote-module__quzrGW__authorBadge",
  "colorButton": "StickyNote-module__quzrGW__colorButton",
  "colorOption": "StickyNote-module__quzrGW__colorOption",
  "colorPicker": "StickyNote-module__quzrGW__colorPicker",
  "deleteButton": "StickyNote-module__quzrGW__deleteButton",
  "groupBadge": "StickyNote-module__quzrGW__groupBadge",
  "note": "StickyNote-module__quzrGW__note",
  "pinButton": "StickyNote-module__quzrGW__pinButton",
  "pinned": "StickyNote-module__quzrGW__pinned",
  "textarea": "StickyNote-module__quzrGW__textarea",
});
}),
"[project]/02_Projects/02_1_App_brain-storming/src/components/StickyNote.js [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>StickyNote
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/components/StickyNote.module.css [app-client] (css module)");
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
function StickyNote({ note, onUpdate, onDelete, scale, onMouseDown, onMouseUp }) {
    _s();
    const [isDragging, setIsDragging] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const noteRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const offset = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])({
        x: 0,
        y: 0
    });
    const handleMouseDown = (e)=>{
        if (onMouseDown) onMouseDown(e); // Propagate to parent for line drawing
        if (e.defaultPrevented || e.altKey) return; // Don't drag if line drawing
        if (note.pinned) return; // Don't drag if pinned
        if (e.target.tagName === "TEXTAREA" || e.target.closest('button')) return; // Allow text selection and button clicks
        e.stopPropagation(); // Prevent board scroll when dragging note
        e.preventDefault(); // Also prevent default to ensure board drag doesn't start
        setIsDragging(true);
        const rect = noteRef.current.getBoundingClientRect();
        offset.current = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    };
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
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
    const [showColorPicker, setShowColorPicker] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const changeColor = (newColor)=>{
        onUpdate({
            ...note,
            color: newColor
        });
        setShowColorPicker(false);
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        ref: noteRef,
        "data-sticky-note": "true",
        className: `${__TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].note} ${note.pinned ? __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].pinned : ''}`,
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
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].pinButton,
                onClick: togglePin,
                onMouseDown: (e)=>e.stopPropagation(),
                title: note.pinned ? "ピン留めを外す" : "ピン留めする",
                children: note.pinned ? "📌" : "📍"
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/StickyNote.js",
                lineNumber: 87,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].colorButton,
                onClick: ()=>setShowColorPicker(!showColorPicker),
                onMouseDown: (e)=>e.stopPropagation(),
                title: "色を変更",
                children: "🎨"
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/StickyNote.js",
                lineNumber: 95,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].deleteButton,
                onClick: (e)=>{
                    e.stopPropagation();
                    if (window.confirm("この付箋を削除してもよろしいですか？")) {
                        onDelete(note.id);
                    }
                },
                onMouseDown: (e)=>e.stopPropagation(),
                title: "削除",
                children: "🗑️"
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/StickyNote.js",
                lineNumber: 103,
                columnNumber: 13
            }, this),
            showColorPicker && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].colorPicker,
                children: COLORS.map((c)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].colorOption,
                        style: {
                            backgroundColor: c
                        },
                        onClick: ()=>changeColor(c),
                        onMouseDown: (e)=>e.stopPropagation()
                    }, c, false, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/StickyNote.js",
                        lineNumber: 119,
                        columnNumber: 25
                    }, this))
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/StickyNote.js",
                lineNumber: 117,
                columnNumber: 17
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("textarea", {
                value: note.text,
                onChange: (e)=>onUpdate({
                        ...note,
                        text: e.target.value
                    }),
                placeholder: "Type here...",
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].textarea
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/StickyNote.js",
                lineNumber: 129,
                columnNumber: 13
            }, this),
            note.groupId && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].groupBadge,
                title: `Group ID: ${note.groupId}`,
                children: "🔗 Group"
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/StickyNote.js",
                lineNumber: 136,
                columnNumber: 17
            }, this),
            note.author && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$StickyNote$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].authorBadge,
                title: `作成者: ${note.author}`,
                children: note.author
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/StickyNote.js",
                lineNumber: 141,
                columnNumber: 17
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/StickyNote.js",
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
"[project]/02_Projects/02_1_App_brain-storming/src/components/BoardCanvas.js [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>BoardCanvas
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$BoardCanvas$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/components/BoardCanvas.module.css [app-client] (css module)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$StickyNote$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/components/StickyNote.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
;
;
;
function BoardCanvas({ notes, lines, onUpdateNote, onDeleteNote, onAddLine, scale }) {
    _s();
    const [drawingLine, setDrawingLine] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null); // { startNoteId, startX, startY, currentX, currentY }
    // Handle line drawing logic here if needed, or keep it simple for now
    // For MVP, we'll just render notes and lines
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$BoardCanvas$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].canvas,
        style: {
            transform: `scale(${scale})`,
            transformOrigin: "0 0",
            width: "4000px",
            height: "4000px"
        },
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$BoardCanvas$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].svgLayer,
                children: lines.map((line, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("line", {
                        x1: line.x1,
                        y1: line.y1,
                        x2: line.x2,
                        y2: line.y2,
                        stroke: "#333",
                        strokeWidth: "2"
                    }, i, false, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/BoardCanvas.js",
                        lineNumber: 23,
                        columnNumber: 21
                    }, this))
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/BoardCanvas.js",
                lineNumber: 21,
                columnNumber: 13
            }, this),
            notes.map((note)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$StickyNote$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                    note: note,
                    onUpdate: onUpdateNote,
                    onDelete: onDeleteNote,
                    scale: scale
                }, note.id, false, {
                    fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/BoardCanvas.js",
                    lineNumber: 36,
                    columnNumber: 17
                }, this))
        ]
    }, void 0, true, {
        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/BoardCanvas.js",
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
"[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.module.css [app-client] (css module)", ((__turbopack_context__) => {

__turbopack_context__.v({
  "active": "Toolbar-module__We2rOW__active",
  "addButton": "Toolbar-module__We2rOW__addButton",
  "colorBtn": "Toolbar-module__We2rOW__colorBtn",
  "divider": "Toolbar-module__We2rOW__divider",
  "group": "Toolbar-module__We2rOW__group",
  "toolbar": "Toolbar-module__We2rOW__toolbar",
});
}),
"[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>Toolbar
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.module.css [app-client] (css module)");
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
function Toolbar({ onAddNote, color, setColor, scale, setScale, onDownload, onUpload, onToggleCommentPanel, onCenter, onToggleParticipants }) {
    _s();
    const fileInputRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const handleFileUpload = (e)=>{
        const file = e.target.files?.[0];
        if (file) {
            onUpload(file);
            e.target.value = ''; // Reset input
        }
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].toolbar,
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].group,
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                    onClick: onAddNote,
                    className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].addButton,
                    children: "+ 付箋"
                }, void 0, false, {
                    fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                    lineNumber: 30,
                    columnNumber: 17
                }, this)
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                lineNumber: 29,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].divider
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                lineNumber: 35,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].group,
                children: COLORS.map((c)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        className: `${__TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].colorBtn} ${color === c ? __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].active : ""}`,
                        style: {
                            backgroundColor: c
                        },
                        onClick: ()=>setColor(c)
                    }, c, false, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                        lineNumber: 39,
                        columnNumber: 21
                    }, this))
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                lineNumber: 37,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].divider
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                lineNumber: 48,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].group,
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        onClick: ()=>setScale((s)=>Math.max(0.5, s - 0.1)),
                        children: "-"
                    }, void 0, false, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                        lineNumber: 51,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        children: [
                            Math.round(scale * 100),
                            "%"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                        lineNumber: 52,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        onClick: ()=>setScale((s)=>Math.min(2, s + 0.1)),
                        children: "+"
                    }, void 0, false, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                        lineNumber: 53,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                lineNumber: 50,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].divider
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                lineNumber: 56,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].group,
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        onClick: onDownload,
                        title: "ボードをダウンロード",
                        children: "💾"
                    }, void 0, false, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                        lineNumber: 59,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
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
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                        lineNumber: 60,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        onClick: ()=>document.querySelector('input[type="file"]')?.click(),
                        title: "ボードをアップロード",
                        children: "📂"
                    }, void 0, false, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                        lineNumber: 67,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                lineNumber: 58,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].divider
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                lineNumber: 70,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].group,
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                    onClick: onCenter,
                    title: "中央に戻る",
                    children: "🎯"
                }, void 0, false, {
                    fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                    lineNumber: 73,
                    columnNumber: 17
                }, this)
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                lineNumber: 72,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].divider
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                lineNumber: 76,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].group,
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                    onClick: onToggleCommentPanel,
                    title: "コメント一覧",
                    children: "📝"
                }, void 0, false, {
                    fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                    lineNumber: 79,
                    columnNumber: 17
                }, this)
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                lineNumber: 78,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].divider
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                lineNumber: 82,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].group,
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                    onClick: onToggleParticipants,
                    title: "参加者リスト",
                    children: "👥"
                }, void 0, false, {
                    fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                    lineNumber: 85,
                    columnNumber: 17
                }, this)
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
                lineNumber: 84,
                columnNumber: 13
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js",
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
"[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.module.css [app-client] (css module)", ((__turbopack_context__) => {

__turbopack_context__.v({
  "actionButtons": "CommentListPanel-module__3hAxzG__actionButtons",
  "actions": "CommentListPanel-module__3hAxzG__actions",
  "checkbox": "CommentListPanel-module__3hAxzG__checkbox",
  "closeButton": "CommentListPanel-module__3hAxzG__closeButton",
  "groupBadge": "CommentListPanel-module__3hAxzG__groupBadge",
  "groupButton": "CommentListPanel-module__3hAxzG__groupButton",
  "header": "CommentListPanel-module__3hAxzG__header",
  "noteItem": "CommentListPanel-module__3hAxzG__noteItem",
  "noteList": "CommentListPanel-module__3hAxzG__noteList",
  "notePreview": "CommentListPanel-module__3hAxzG__notePreview",
  "noteText": "CommentListPanel-module__3hAxzG__noteText",
  "panel": "CommentListPanel-module__3hAxzG__panel",
  "pinnedBadge": "CommentListPanel-module__3hAxzG__pinnedBadge",
  "selected": "CommentListPanel-module__3hAxzG__selected",
  "ungroupButton": "CommentListPanel-module__3hAxzG__ungroupButton",
});
}),
"[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>CommentListPanel
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.module.css [app-client] (css module)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
function CommentListPanel({ notes, onJumpToNote, onGroupNotes, onUngroupNotes, onClose }) {
    _s();
    const [selectedNotes, setSelectedNotes] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
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
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].panel,
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].header,
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                        children: "コメント一覧"
                    }, void 0, false, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js",
                        lineNumber: 38,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        onClick: onClose,
                        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].closeButton,
                        children: "✕"
                    }, void 0, false, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js",
                        lineNumber: 39,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js",
                lineNumber: 37,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].actions,
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        children: [
                            selectedNotes.length,
                            " 個選択中"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js",
                        lineNumber: 43,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].actionButtons,
                        children: [
                            selectedNotes.length >= 2 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: handleGroupSelected,
                                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].groupButton,
                                children: "グループ化"
                            }, void 0, false, {
                                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js",
                                lineNumber: 46,
                                columnNumber: 25
                            }, this),
                            selectedNotes.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: handleUngroupSelected,
                                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].ungroupButton,
                                children: "解除"
                            }, void 0, false, {
                                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js",
                                lineNumber: 51,
                                columnNumber: 25
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js",
                        lineNumber: 44,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js",
                lineNumber: 42,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].noteList,
                children: notes.map((note)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: `${__TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].noteItem} ${selectedNotes.includes(note.id) ? __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].selected : ''}`,
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                type: "checkbox",
                                checked: selectedNotes.includes(note.id),
                                onChange: ()=>toggleSelection(note.id),
                                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].checkbox
                            }, void 0, false, {
                                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js",
                                lineNumber: 64,
                                columnNumber: 25
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].notePreview,
                                style: {
                                    backgroundColor: note.color
                                },
                                onClick: ()=>onJumpToNote(note),
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].noteText,
                                        children: note.text || "(空白)"
                                    }, void 0, false, {
                                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js",
                                        lineNumber: 75,
                                        columnNumber: 29
                                    }, this),
                                    note.pinned && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].pinnedBadge,
                                        children: "📌"
                                    }, void 0, false, {
                                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js",
                                        lineNumber: 78,
                                        columnNumber: 45
                                    }, this),
                                    note.groupId && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].groupBadge,
                                        children: [
                                            "Group ",
                                            note.groupId
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js",
                                        lineNumber: 79,
                                        columnNumber: 46
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js",
                                lineNumber: 70,
                                columnNumber: 25
                            }, this)
                        ]
                    }, note.id, true, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js",
                        lineNumber: 60,
                        columnNumber: 21
                    }, this))
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js",
                lineNumber: 58,
                columnNumber: 13
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js",
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
"[project]/02_Projects/02_1_App_brain-storming/src/components/UserDialog.module.css [app-client] (css module)", ((__turbopack_context__) => {

__turbopack_context__.v({
  "button": "UserDialog-module__XDPH8a__button",
  "description": "UserDialog-module__XDPH8a__description",
  "dialog": "UserDialog-module__XDPH8a__dialog",
  "error": "UserDialog-module__XDPH8a__error",
  "fadeIn": "UserDialog-module__XDPH8a__fadeIn",
  "input": "UserDialog-module__XDPH8a__input",
  "note": "UserDialog-module__XDPH8a__note",
  "overlay": "UserDialog-module__XDPH8a__overlay",
  "slideUp": "UserDialog-module__XDPH8a__slideUp",
  "title": "UserDialog-module__XDPH8a__title",
});
}),
"[project]/02_Projects/02_1_App_brain-storming/src/components/UserDialog.js [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>UserDialog
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$UserDialog$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/components/UserDialog.module.css [app-client] (css module)");
;
var _s = __turbopack_context__.k.signature();
;
;
function UserDialog({ onSubmit }) {
    _s();
    const [username, setUsername] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("");
    const [error, setError] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("");
    const handleSubmit = (e)=>{
        e.preventDefault();
        const trimmedName = username.trim();
        if (!trimmedName) {
            setError("名前を入力してください");
            return;
        }
        if (trimmedName.length > 20) {
            setError("名前は20文字以内にしてください");
            return;
        }
        onSubmit(trimmedName);
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$UserDialog$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].overlay,
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$UserDialog$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].dialog,
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                    className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$UserDialog$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].title,
                    children: "ボードに参加"
                }, void 0, false, {
                    fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/UserDialog.js",
                    lineNumber: 29,
                    columnNumber: 17
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                    className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$UserDialog$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].description,
                    children: "あなたの名前を入力してください"
                }, void 0, false, {
                    fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/UserDialog.js",
                    lineNumber: 30,
                    columnNumber: 17
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("form", {
                    onSubmit: handleSubmit,
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                            type: "text",
                            value: username,
                            onChange: (e)=>{
                                setUsername(e.target.value);
                                setError("");
                            },
                            placeholder: "例：田中太郎",
                            className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$UserDialog$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].input,
                            autoFocus: true,
                            maxLength: 20
                        }, void 0, false, {
                            fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/UserDialog.js",
                            lineNumber: 35,
                            columnNumber: 21
                        }, this),
                        error && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$UserDialog$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].error,
                            children: error
                        }, void 0, false, {
                            fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/UserDialog.js",
                            lineNumber: 49,
                            columnNumber: 25
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                            type: "submit",
                            className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$UserDialog$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].button,
                            children: "参加する"
                        }, void 0, false, {
                            fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/UserDialog.js",
                            lineNumber: 52,
                            columnNumber: 21
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/UserDialog.js",
                    lineNumber: 34,
                    columnNumber: 17
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                    className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$UserDialog$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].note,
                    children: "※この名前は付箋の作成者として表示されます"
                }, void 0, false, {
                    fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/UserDialog.js",
                    lineNumber: 57,
                    columnNumber: 17
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/UserDialog.js",
            lineNumber: 28,
            columnNumber: 13
        }, this)
    }, void 0, false, {
        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/UserDialog.js",
        lineNumber: 27,
        columnNumber: 9
    }, this);
}
_s(UserDialog, "+dcE9wFxfyoZLg456sqQ2H+YfQw=");
_c = UserDialog;
var _c;
__turbopack_context__.k.register(_c, "UserDialog");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/02_Projects/02_1_App_brain-storming/src/components/ParticipantsList.module.css [app-client] (css module)", ((__turbopack_context__) => {

__turbopack_context__.v({
  "avatar": "ParticipantsList-module__IOaoEq__avatar",
  "closeButton": "ParticipantsList-module__IOaoEq__closeButton",
  "empty": "ParticipantsList-module__IOaoEq__empty",
  "header": "ParticipantsList-module__IOaoEq__header",
  "info": "ParticipantsList-module__IOaoEq__info",
  "list": "ParticipantsList-module__IOaoEq__list",
  "name": "ParticipantsList-module__IOaoEq__name",
  "panel": "ParticipantsList-module__IOaoEq__panel",
  "participant": "ParticipantsList-module__IOaoEq__participant",
  "slideIn": "ParticipantsList-module__IOaoEq__slideIn",
  "status": "ParticipantsList-module__IOaoEq__status",
  "title": "ParticipantsList-module__IOaoEq__title",
});
}),
"[project]/02_Projects/02_1_App_brain-storming/src/components/ParticipantsList.js [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>ParticipantsList
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$ParticipantsList$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/components/ParticipantsList.module.css [app-client] (css module)");
;
;
function ParticipantsList({ participants, onClose }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$ParticipantsList$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].panel,
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$ParticipantsList$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].header,
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$ParticipantsList$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].title,
                        children: [
                            "👥 参加者 (",
                            participants.length,
                            ")"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/ParticipantsList.js",
                        lineNumber: 7,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        onClick: onClose,
                        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$ParticipantsList$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].closeButton,
                        children: "✕"
                    }, void 0, false, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/ParticipantsList.js",
                        lineNumber: 10,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/ParticipantsList.js",
                lineNumber: 6,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$ParticipantsList$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].list,
                children: participants.length === 0 ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$ParticipantsList$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].empty,
                    children: "参加者がいません"
                }, void 0, false, {
                    fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/ParticipantsList.js",
                    lineNumber: 17,
                    columnNumber: 21
                }, this) : participants.map((participant)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$ParticipantsList$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].participant,
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$ParticipantsList$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].avatar,
                                children: participant.username.charAt(0).toUpperCase()
                            }, void 0, false, {
                                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/ParticipantsList.js",
                                lineNumber: 23,
                                columnNumber: 29
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$ParticipantsList$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].info,
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$ParticipantsList$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].name,
                                        children: participant.username
                                    }, void 0, false, {
                                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/ParticipantsList.js",
                                        lineNumber: 27,
                                        columnNumber: 33
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$ParticipantsList$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].status,
                                        children: "🟢 オンライン"
                                    }, void 0, false, {
                                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/ParticipantsList.js",
                                        lineNumber: 28,
                                        columnNumber: 33
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/ParticipantsList.js",
                                lineNumber: 26,
                                columnNumber: 29
                            }, this)
                        ]
                    }, participant.socketId, true, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/ParticipantsList.js",
                        lineNumber: 22,
                        columnNumber: 25
                    }, this))
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/ParticipantsList.js",
                lineNumber: 15,
                columnNumber: 13
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/components/ParticipantsList.js",
        lineNumber: 5,
        columnNumber: 9
    }, this);
}
_c = ParticipantsList;
var _c;
__turbopack_context__.k.register(_c, "ParticipantsList");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>BoardPage
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/navigation.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$socket$2e$io$2d$client$2f$build$2f$esm$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/socket.io-client/build/esm/index.js [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$app$2f$board$2f5b$id$5d2f$page$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.module.css [app-client] (css module)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$BoardCanvas$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/components/BoardCanvas.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/components/Toolbar.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/components/CommentListPanel.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$UserDialog$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/components/UserDialog.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$ParticipantsList$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/components/ParticipantsList.js [app-client] (ecmascript)");
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
;
;
const SOCKET_SERVER_URL = "http://localhost:3000"; // Ensure this matches your server
const TRASH_AREA = {
    x: 3600,
    y: 3600
};
const TRASH_COLOR = "#e0e0e0";
let socket;
function BoardPage() {
    _s();
    const params = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useParams"])();
    const boardId = params?.id;
    const [notes, setNotes] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [lines, setLines] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [color, setColor] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("#ffeb3b"); // Default yellow
    const [isConnected, setIsConnected] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [scale, setScale] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(1);
    const [title, setTitle] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("");
    const [showCommentPanel, setShowCommentPanel] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [username, setUsername] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("");
    const [showUserDialog, setShowUserDialog] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [participants, setParticipants] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [showParticipantsList, setShowParticipantsList] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const boardContainerRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "BoardPage.useEffect": ()=>{
            if (!boardId) return;
            // Check if user has a saved username
            const savedUsername = localStorage.getItem('brainstorming-username');
            if (savedUsername) {
                setUsername(savedUsername);
            } else {
                setShowUserDialog(true);
            }
            // Initialize Socket.io connection with reconnection options
            socket = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$socket$2e$io$2d$client$2f$build$2f$esm$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["default"])({
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
                    // Send user info if username is set
                    const currentUsername = localStorage.getItem('brainstorming-username');
                    if (currentUsername) {
                        socket.emit("user-join", {
                            boardId,
                            username: currentUsername
                        });
                    }
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
            socket.on("note-deleted", {
                "BoardPage.useEffect": (noteId)=>{
                    setNotes({
                        "BoardPage.useEffect": (prev)=>prev.filter({
                                "BoardPage.useEffect": (n)=>n.id !== noteId
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
            // User events
            socket.on("users-list", {
                "BoardPage.useEffect": (usersList)=>{
                    setParticipants(usersList);
                }
            }["BoardPage.useEffect"]);
            socket.on("user-joined", {
                "BoardPage.useEffect": ({ username: newUsername })=>{
                    console.log(`${newUsername} joined the board`);
                }
            }["BoardPage.useEffect"]);
            socket.on("user-left", {
                "BoardPage.useEffect": ({ username: leftUsername })=>{
                    console.log(`${leftUsername} left the board`);
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
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
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
    const handleUserSubmit = (newUsername)=>{
        setUsername(newUsername);
        localStorage.setItem('brainstorming-username', newUsername);
        setShowUserDialog(false);
        // Send user-join event to server
        if (socket && socket.connected) {
            socket.emit("user-join", {
                boardId,
                username: newUsername
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
            pinned: false,
            author: username,
            createdAt: Date.now()
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
    const notesRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(notes);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "BoardPage.useEffect": ()=>{
            notesRef.current = notes;
        }
    }["BoardPage.useEffect"], [
        notes
    ]);
    const updateTimeout = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const updateNote = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
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
            // Logic for restoring from trash (logical deletion recovery)
            if (originalNote && originalNote.groupId === 'trash') {
                const isMoved = updatedNote.x !== originalNote.x || updatedNote.y !== originalNote.y;
                const isColorChanged = updatedNote.color !== TRASH_COLOR;
                if (isMoved || isColorChanged) {
                    // Restore from trash if moved or color changed
                    updatedNote.groupId = null;
                // If it was only moved but color is still gray, keep it gray unless user changed it?
                // Spec says "manually change color AND move". Let's assume ANY action restores it.
                // If color changed, it's already updated in updatedNote.color
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
    const deleteNote = (noteId)=>{
        // Logical deletion: Move to trash area and change color
        const noteToDelete = notes.find((n)=>n.id === noteId);
        if (!noteToDelete) return;
        const offset = Math.random() * 20 - 10;
        const trashNote = {
            ...noteToDelete,
            color: TRASH_COLOR,
            groupId: 'trash',
            x: TRASH_AREA.x + offset,
            y: TRASH_AREA.y + offset,
            pinned: false // Unpin if pinned
        };
        // Optimistic update
        setNotes((prev)=>prev.map((n)=>n.id === noteId ? trashNote : n));
        socket.emit("update-note", {
            boardId,
            note: trashNote
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
        // Arrange notes in a pile (slightly overlapped)
        const updatedNotes = selectedNotes.map((note, index)=>{
            // Offset each note slightly to create a messy pile effect
            const offset = index * 10;
            const totalOffset = (selectedNotes.length - 1) * 10 / 2;
            const newX = centerX + offset - totalOffset;
            const newY = centerY + offset - totalOffset;
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
        const updatedNotes = notes.filter((n)=>noteIds.includes(n.id)).map((n)=>{
            return {
                ...n,
                groupId: null
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
        alert(`${noteIds.length}個の付箋のグループ化を解除しました`);
    };
    const [isDraggingBoard, setIsDraggingBoard] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const dragStart = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])({
        x: 0,
        y: 0
    });
    const scrollStart = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])({
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
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$app$2f$board$2f5b$id$5d2f$page$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].boardContainer,
        ref: boardContainerRef,
        onMouseDown: handleMouseDown,
        onMouseMove: handleMouseMove,
        onMouseUp: handleMouseUp,
        onMouseLeave: handleMouseUp,
        style: {
            cursor: 'grab'
        },
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$app$2f$board$2f5b$id$5d2f$page$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].header,
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                        type: "text",
                        value: title,
                        onChange: (e)=>setTitle(e.target.value),
                        placeholder: "ボードタイトルを入力...",
                        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$app$2f$board$2f5b$id$5d2f$page$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].titleInput
                    }, void 0, false, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                        lineNumber: 465,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$app$2f$board$2f5b$id$5d2f$page$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].status,
                        children: isConnected ? "🟢 Online" : "🔴 Offline"
                    }, void 0, false, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                        lineNumber: 472,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                lineNumber: 464,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$Toolbar$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                onAddNote: addNote,
                color: color,
                setColor: setColor,
                scale: scale,
                setScale: setScale,
                onDownload: handleDownload,
                onUpload: handleUpload,
                onToggleCommentPanel: ()=>setShowCommentPanel(!showCommentPanel),
                onCenter: handleCenter,
                onToggleParticipants: ()=>setShowParticipantsList(!showParticipantsList)
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                lineNumber: 477,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$app$2f$board$2f5b$id$5d2f$page$2e$module$2e$css__$5b$app$2d$client$5d$__$28$css__module$29$__["default"].canvasWrapper,
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$BoardCanvas$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                    notes: notes,
                    lines: lines,
                    onUpdateNote: updateNote,
                    onDeleteNote: deleteNote,
                    onAddLine: addLine,
                    scale: scale
                }, void 0, false, {
                    fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                    lineNumber: 491,
                    columnNumber: 17
                }, this)
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                lineNumber: 490,
                columnNumber: 13
            }, this),
            showCommentPanel && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$CommentListPanel$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                notes: notes,
                onJumpToNote: handleJumpToNote,
                onGroupNotes: handleGroupNotes,
                onUngroupNotes: handleUngroupNotes,
                onClose: ()=>setShowCommentPanel(false)
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                lineNumber: 502,
                columnNumber: 17
            }, this),
            showParticipantsList && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$ParticipantsList$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                participants: participants,
                onClose: ()=>setShowParticipantsList(false)
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                lineNumber: 512,
                columnNumber: 17
            }, this),
            showUserDialog && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$components$2f$UserDialog$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                onSubmit: handleUserSubmit
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                lineNumber: 519,
                columnNumber: 17
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
        lineNumber: 455,
        columnNumber: 9
    }, this);
}
_s(BoardPage, "SYs7lIZEPTb8lwU587QWqX85ofY=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useParams"]
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

//# sourceMappingURL=02_Projects_02_1_App_brain-storming_src_5396b2fa._.js.map