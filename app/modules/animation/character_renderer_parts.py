"""Character Renderer Sub-Components (G5.2.3.1, G5.2.3.2 & G5.2.3.3).

Contains the modular sub-renderers for Dark Myth stickman figures:
- HumanoidBodyRenderer: 14-joint, 13-bone base stickman skeleton.
- FaceFeatureRenderer: Facial features (Wukong fiery eyes, Erlang Third Eye, warrior visors).
- AccessoriesRenderer: Back and front accessories (Kim Cô, pheasant feathers, cape/scarf, helmets, pauldrons).
- WeaponRenderer: Primary and secondary two-handed weapon rendering (Ruyi Staff, Spear, Halberd).
- composite_character: Strict layer compositing helper (Back -> Body -> Weapon -> Face -> Front).
"""

from dataclasses import dataclass
import math
from typing import Optional, Union

import numpy as np
from PIL import Image, ImageDraw

from app.core.logger import get_logger
from app.modules.animation.buddha_palm_renderer import BuddhaPalmRenderer
from app.modules.animation.pose_catalog import PoseCatalog, PoseDefinition
from app.modules.animation.stickman_models import (
    CoordinateManager,
    HumanoidSkeleton,
    JointType,
    Point2D,
    StickmanCharacter,
    StickmanPose,
    WeaponType,
)
from app.schemas.scene_schema import CharacterSkin

logger = get_logger("character_renderer_parts")


class HumanoidBodyRenderer:
    """
    Renders the foundational stickman humanoid body on a transparent RGBA canvas.

    Draws:
      - 13 bone segments with ink stroke width scaled proportionally.
      - Smooth circular joint caps preventing angular junction gaps.
      - Solid dark ink circular head.
      - Small hand/wrist caps and foot caps.
      - Strict transparent background (alpha = 0).
      - Strict coordinate contract: canvas_position is Pelvis canvas coordinate.
    """

    DEFAULT_CANVAS_SIZE: tuple[int, int] = (1080, 1920)

    def __init__(self) -> None:
        pass

    def transform_joints(
        self,
        pose: StickmanPose,
        canvas_position: Point2D,
        facing: int = 1,
        scale: float = 1.0,
    ) -> dict[JointType, Point2D]:
        """
        Transform all 14 pose joints from Local Space to Canvas Space.

        Canvas Position is strictly the Canvas coordinate of the PELVIS joint.
        Facing must be +1 (looking right) or -1 (looking left).
        """
        if facing not in (+1, -1):
            raise ValueError(f"Facing must be +1 or -1, got {facing}")
        if scale <= 0.1 or scale > 5.0 or not math.isfinite(scale):
            raise ValueError(f"scale must be in range (0.1, 5.0], got {scale}")

        canvas_pose = CoordinateManager.transform_pose_to_canvas(
            pose=pose,
            pelvis_canvas=canvas_position,
            facing=facing,
            scale=scale,
        )
        return canvas_pose.joints

    def get_joint_bounding_box(
        self,
        pose: StickmanPose,
        canvas_position: Point2D,
        facing: int = 1,
        scale: float = 1.0,
        canvas_size: tuple[int, int] = DEFAULT_CANVAS_SIZE,
    ) -> tuple[int, int, int, int]:
        """
        Compute the geometric axis-aligned bounding box (min_x, min_y, max_x, max_y)
        derived purely from the 14 joint coordinates (Local Space -> Canvas Space).
        """
        joints = self.transform_joints(
            pose=pose,
            canvas_position=canvas_position,
            facing=facing,
            scale=scale,
        )
        xs = [pt.x for pt in joints.values()]
        ys = [pt.y for pt in joints.values()]

        min_x = int(math.floor(min(xs)))
        max_x = int(math.ceil(max(xs)))
        min_y = int(math.floor(min(ys)))
        max_y = int(math.ceil(max(ys)))

        width, height = canvas_size
        return (
            max(0, min(min_x, width)),
            max(0, min(min_y, height)),
            max(0, min(max_x, width)),
            max(0, min(max_y, height)),
        )

    def get_bounding_box(
        self,
        character: StickmanCharacter,
        pose: StickmanPose,
        canvas_position: Point2D,
        facing: int = 1,
        canvas_size: tuple[int, int] = DEFAULT_CANVAS_SIZE,
    ) -> tuple[int, int, int, int]:
        """
        Compute the exact analytical axis-aligned bounding box (min_x, min_y, max_x, max_y)
        of the rendered stickman body primitives (head circle, 13 bone strokes, joint caps,
        wrist caps, and ankle caps), clipped to canvas dimensions.
        """
        scale = character.scale
        joints = self.transform_joints(
            pose=pose,
            canvas_position=canvas_position,
            facing=facing,
            scale=scale,
        )

        boxes: list[tuple[float, float, float, float]] = []

        # 1. Head circle primitive
        head_pt = joints[JointType.HEAD]
        head_r = CoordinateManager.HEAD_RADIUS * scale
        boxes.append(
            (head_pt.x - head_r, head_pt.y - head_r, head_pt.x + head_r, head_pt.y + head_r)
        )

        # 2. 13 Bone limb segments and joint caps
        for bone in HumanoidSkeleton.BONES:
            p1 = joints[bone.parent]
            p2 = joints[bone.child]
            lw = max(2, round(bone.stroke_width * scale))
            r = lw / 2.0
            boxes.append(
                (
                    min(p1.x, p2.x) - r,
                    min(p1.y, p2.y) - r,
                    max(p1.x, p2.x) + r,
                    max(p1.y, p2.y) + r,
                )
            )

        # 3. Wrist caps
        wrist_r = max(3.0, 5.0 * scale)
        for wj in (JointType.WRIST_L, JointType.WRIST_R):
            pt = joints[wj]
            boxes.append((pt.x - wrist_r, pt.y - wrist_r, pt.x + wrist_r, pt.y + wrist_r))

        # 4. Ankle / Foot caps
        ankle_r = max(3.0, CoordinateManager.FOOT_EXTENT * scale)
        for aj in (JointType.ANKLE_L, JointType.ANKLE_R):
            pt = joints[aj]
            boxes.append((pt.x - ankle_r, pt.y - ankle_r, pt.x + ankle_r, pt.y + ankle_r))

        min_x = int(math.floor(min(b[0] for b in boxes)))
        min_y = int(math.floor(min(b[1] for b in boxes)))
        max_x = int(math.ceil(max(b[2] for b in boxes)))
        max_y = int(math.ceil(max(b[3] for b in boxes)))

        width, height = canvas_size
        return (
            max(0, min(min_x, width)),
            max(0, min(min_y, height)),
            max(0, min(max_x, width)),
            max(0, min(max_y, height)),
        )

    def get_padded_bounding_box(
        self,
        character: StickmanCharacter,
        pose: StickmanPose,
        canvas_position: Point2D,
        facing: int = 1,
        padding: float = 10.0,
        canvas_size: tuple[int, int] = DEFAULT_CANVAS_SIZE,
    ) -> tuple[int, int, int, int]:
        """
        Compute the primitive bounding box expanded by a specified external padding.
        """
        min_x, min_y, max_x, max_y = self.get_bounding_box(
            character, pose, canvas_position, facing, canvas_size
        )
        pad = int(math.ceil(padding))
        width, height = canvas_size
        return (
            max(0, min_x - pad),
            max(0, min_y - pad),
            min(width, max_x + pad),
            min(height, max_y + pad),
        )

    def render_body(
        self,
        character: StickmanCharacter,
        pose: StickmanPose,
        canvas_position: Point2D,
        facing: int = 1,
        canvas_size: tuple[int, int] = DEFAULT_CANVAS_SIZE,
    ) -> Image.Image:
        """
        Render the stickman humanoid body on an isolated transparent RGBA canvas.

        Parameters:
          character: StickmanCharacter metadata containing stroke_color and scale.
          pose: StickmanPose containing local joint positions.
          canvas_position: Point2D representing the PELVIS canvas coordinate.
          facing: +1 (looks right) or -1 (looks left).
          canvas_size: (width, height) of the output canvas.

        Returns:
          PIL.Image.Image in 'RGBA' mode with completely transparent background.
        """
        width, height = canvas_size
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 1. Coordinate transformation
        scale = character.scale
        stroke_color = character.stroke_color  # (R, G, B, A)
        joints = self.transform_joints(
            pose=pose,
            canvas_position=canvas_position,
            facing=facing,
            scale=scale,
        )

        # 2. Draw 13 bone segments with smooth rounded connection caps
        for bone in HumanoidSkeleton.BONES:
            p_parent = joints[bone.parent]
            p_child = joints[bone.child]
            line_width = max(2, round(bone.stroke_width * scale))

            # Draw the bone limb
            draw.line(
                [(p_parent.x, p_parent.y), (p_child.x, p_child.y)],
                fill=stroke_color,
                width=line_width,
            )

            # Cap the endpoints with circles of radius = line_width / 2 to avoid angular gaps
            cap_r = line_width / 2.0
            for pt in (p_parent, p_child):
                draw.ellipse(
                    [pt.x - cap_r, pt.y - cap_r, pt.x + cap_r, pt.y + cap_r],
                    fill=stroke_color,
                )

        # 3. Draw Hands / Wrists caps
        wrist_r = max(3.0, 5.0 * scale)
        for wrist_joint in (JointType.WRIST_L, JointType.WRIST_R):
            pt = joints[wrist_joint]
            draw.ellipse(
                [pt.x - wrist_r, pt.y - wrist_r, pt.x + wrist_r, pt.y + wrist_r],
                fill=stroke_color,
            )

        # 4. Draw Feet / Ankles caps
        ankle_r = max(3.0, CoordinateManager.FOOT_EXTENT * scale)
        for ankle_joint in (JointType.ANKLE_L, JointType.ANKLE_R):
            pt = joints[ankle_joint]
            draw.ellipse(
                [pt.x - ankle_r, pt.y - ankle_r, pt.x + ankle_r, pt.y + ankle_r],
                fill=stroke_color,
            )

        # 5. Draw solid circular head
        head_pt = joints[JointType.HEAD]
        head_radius = CoordinateManager.HEAD_RADIUS * scale
        draw.ellipse(
            [
                head_pt.x - head_radius,
                head_pt.y - head_radius,
                head_pt.x + head_radius,
                head_pt.y + head_radius,
            ],
            fill=stroke_color,
        )

        return img


# ==============================================================================
# G5.2.3.2 – FACE FEATURE & ACCESSORIES RENDERERS
# ==============================================================================


def evaluate_cubic_bezier(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    num_points: int = 60,
) -> list[tuple[float, float]]:
    """
    Compute points along a cubic Bezier curve B(t) for t in [0, 1].

    Guaranteed finite floating point coordinates; no NaN or Infinity.
    """
    pts: list[tuple[float, float]] = []
    for i in range(num_points + 1):
        t = i / num_points
        u = 1.0 - t
        x = (u**3 * p0[0]) + (3 * u**2 * t * p1[0]) + (3 * u * t**2 * p2[0]) + (t**3 * p3[0])
        y = (u**3 * p0[1]) + (3 * u**2 * t * p1[1]) + (3 * u * t**2 * p2[1]) + (t**3 * p3[1])
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError(f"Bezier evaluation generated non-finite coordinate: x={x}, y={y}")
        pts.append((x, y))
    return pts


def calculate_bezier_length(points: list[tuple[float, float]]) -> float:
    """Calculate the total Euclidean arc length of a sampled polyline."""
    if len(points) < 2:
        return 0.0
    return sum(
        math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1])
        for i in range(len(points) - 1)
    )


class FaceFeatureRenderer:
    """
    Renders facial features (eyes, divine eye, visor slits) on transparent RGBA canvases.

    Dark Myth Features:
      - Dark Wukong: Fierce glowing red eyes (#FF1E1E) with sharp slant and pupil highlight.
      - Erlang Shen: Divine Third Eye (#FFD700) vertical diamond slit in center forehead, plus cyan steel eye.
      - Celestial General: Stern pale-blue visor slit (#E2E8F0 / #63B3ED).
      - Celestial Soldier: Simple pale-steel visor slit (#CBD5E0).
    """

    def __init__(self) -> None:
        self._body_renderer = HumanoidBodyRenderer()

    def render_face_features(
        self,
        character: StickmanCharacter,
        pose: StickmanPose,
        canvas_position: Point2D,
        facing: int = 1,
        canvas_size: tuple[int, int] = HumanoidBodyRenderer.DEFAULT_CANVAS_SIZE,
    ) -> Image.Image:
        """
        Render character facial features onto an isolated transparent RGBA canvas.

        Parameters:
          character: StickmanCharacter with skin, scale, seed.
          pose: StickmanPose containing local joint positions.
          canvas_position: PELVIS canvas coordinate.
          facing: +1 (looks right) or -1 (looks left).
          canvas_size: Output canvas dimensions (default 1080x1920).
        """
        if facing not in (+1, -1):
            raise ValueError(f"Facing must be +1 or -1, got {facing}")
        scale = character.scale
        if scale <= 0.1 or scale > 5.0 or not math.isfinite(scale):
            raise ValueError(f"scale must be in range (0.1, 5.0], got {scale}")

        width, height = canvas_size
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        joints = self._body_renderer.transform_joints(
            pose=pose,
            canvas_position=canvas_position,
            facing=facing,
            scale=scale,
        )
        head_pt = joints[JointType.HEAD]

        skin = character.skin

        if skin == CharacterSkin.DARK_WUKONG:
            # 1. Dark Wukong: Fierce glowing red eye (#FF1E1E)
            # Positioned forward on face, strictly inside head circle (R = 26 * scale)
            eye_cx = head_pt.x + (8.0 * facing * scale)
            eye_cy = head_pt.y - (2.0 * scale)

            # Fierce sharp eye polygon (slanted upward for aggressive Dark Myth expression)
            eye_pts = [
                (eye_cx - (5.0 * facing * scale), eye_cy + (1.5 * scale)),
                (eye_cx, eye_cy - (3.5 * scale)),
                (eye_cx + (8.0 * facing * scale), eye_cy - (2.0 * scale)),
                (eye_cx + (1.0 * facing * scale), eye_cy + (3.0 * scale)),
            ]
            draw.polygon(eye_pts, fill=(255, 30, 30, 255))
            # Bright inner highlight dot for intense burning pupil
            draw.ellipse(
                [
                    eye_cx - (1.5 * scale),
                    eye_cy - (1.5 * scale),
                    eye_cx + (1.5 * scale),
                    eye_cy + (1.5 * scale),
                ],
                fill=(255, 230, 230, 255),
            )

        elif skin == CharacterSkin.ERLANG_SHEN:
            # 2. Erlang Shen: Divine Third Eye (Thiên Nhãn) in center of forehead
            x3 = head_pt.x + (4.0 * facing * scale)
            y3 = head_pt.y - (6.0 * scale)

            # Vertical golden diamond slit
            diamond = [
                (x3, y3 - (9.0 * scale)),
                (x3 + (3.5 * scale), y3),
                (x3, y3 + (9.0 * scale)),
                (x3 - (3.5 * scale), y3),
            ]
            # Radiant golden outer aura
            draw.polygon(diamond, fill=(255, 215, 0, 255))
            # Bright white-gold inner core
            inner_diamond = [
                (x3, y3 - (6.0 * scale)),
                (x3 + (2.0 * scale), y3),
                (x3, y3 + (6.0 * scale)),
                (x3 - (2.0 * scale), y3),
            ]
            draw.polygon(inner_diamond, fill=(255, 255, 220, 255))
            # Dark vertical pupil slit
            draw.line(
                [(x3, y3 - (5.0 * scale)), (x3, y3 + (5.0 * scale))],
                fill=(25, 25, 35, 255),
                width=max(1, round(1.5 * scale)),
            )

            # Normal warrior eye (lower and forward, cold steel cyan)
            norm_cx = head_pt.x + (11.0 * facing * scale)
            norm_cy = head_pt.y + (3.0 * scale)
            norm_pts = [
                (norm_cx - (4.0 * facing * scale), norm_cy + (1.0 * scale)),
                (norm_cx, norm_cy - (2.0 * scale)),
                (norm_cx + (6.0 * facing * scale), norm_cy),
                (norm_cx + (1.0 * facing * scale), norm_cy + (2.0 * scale)),
            ]
            draw.polygon(norm_pts, fill=(99, 179, 237, 255))

        elif skin == CharacterSkin.CELESTIAL_GENERAL:
            # 3. Celestial General: Resolute pale blue/steel visor slit
            visor_cx = head_pt.x + (9.0 * facing * scale)
            visor_cy = head_pt.y + (1.0 * scale)
            w_v = 8.0 * scale
            h_v = 3.5 * scale
            visor_pts = [
                (visor_cx - (w_v / 2.0 * facing), visor_cy - (h_v / 2.0)),
                (visor_cx + (w_v / 2.0 * facing), visor_cy - (h_v / 2.0)),
                (visor_cx + (w_v / 2.0 * facing), visor_cy + (h_v / 2.0)),
                (visor_cx - (w_v / 2.0 * facing), visor_cy + (h_v / 2.0)),
            ]
            draw.polygon(visor_pts, fill=(226, 232, 240, 255), outline=(99, 179, 237, 255))

        elif skin == CharacterSkin.CELESTIAL_SOLDIER_SQUAD:
            # 4. Celestial Soldier: Simple soldier visor slit
            visor_cx = head_pt.x + (8.0 * facing * scale)
            visor_cy = head_pt.y + (1.0 * scale)
            w_v = 6.0 * scale
            h_v = 2.5 * scale
            visor_pts = [
                (visor_cx - (w_v / 2.0 * facing), visor_cy - (h_v / 2.0)),
                (visor_cx + (w_v / 2.0 * facing), visor_cy - (h_v / 2.0)),
                (visor_cx + (w_v / 2.0 * facing), visor_cy + (h_v / 2.0)),
                (visor_cx - (w_v / 2.0 * facing), visor_cy + (h_v / 2.0)),
            ]
            draw.polygon(visor_pts, fill=(203, 213, 224, 255))

        else:
            # Generic humanoid warrior eye fallback
            eye_cx = head_pt.x + (8.0 * facing * scale)
            eye_cy = head_pt.y
            draw.ellipse(
                [
                    eye_cx - (2.5 * scale),
                    eye_cy - (2.0 * scale),
                    eye_cx + (2.5 * scale),
                    eye_cy + (2.0 * scale),
                ],
                fill=(240, 240, 250, 255),
            )

        return img


class AccessoriesRenderer:
    """
    Renders back and front character accessories on isolated transparent RGBA canvases.

    Layer Division:
      - Back Accessories: Rendered BEHIND the humanoid body (Scarf, Pheasant feathers, Cloaks).
      - Front Accessories: Rendered IN FRONT OF body and face (Kim Cô, Helmets, Shoulder pauldrons).
    """

    def __init__(self) -> None:
        self._body_renderer = HumanoidBodyRenderer()

    def get_feather_bezier_curves(
        self,
        head_pt: Point2D,
        facing: int,
        scale: float,
    ) -> tuple[list[tuple[float, float]], list[tuple[float, float]], float, float]:
        """
        Compute the twin pheasant tail feather Bezier curves for Dark Wukong.

        Returns: (plume1_points, plume2_points, length1, length2)
        """
        flow_dir = -facing

        # Anchor at top-back of head
        p0 = (
            head_pt.x - (6.0 * facing * scale),
            head_pt.y - (20.0 * scale),
        )

        # Plume 1: High arching outer feather (180.0 ± 1.0 px at scale 1.0)
        p1 = (p0[0] + (-21.7 * flow_dir * scale), p0[1] + (-77.0 * scale))
        p2 = (p0[0] + (-84.9 * flow_dir * scale), p0[1] + (-86.8 * scale))
        p3 = (p0[0] + (-130.3 * flow_dir * scale), p0[1] + (-21.7 * scale))
        pts1 = evaluate_cubic_bezier(p0, p1, p2, p3, num_points=60)
        len1 = calculate_bezier_length(pts1)

        # Plume 2: Distinct lower inner feather (180.0 ± 1.0 px at scale 1.0)
        p0_b = (p0[0] - (2.0 * flow_dir * scale), p0[1] + (3.0 * scale))
        p1_b = (p0_b[0] + (-17.0 * flow_dir * scale), p0_b[1] + (-66.0 * scale))
        p2_b = (p0_b[0] + (-82.0 * flow_dir * scale), p0_b[1] + (-78.0 * scale))
        p3_b = (p0_b[0] + (-135.0 * flow_dir * scale), p0_b[1] + (-8.0 * scale))
        pts2 = evaluate_cubic_bezier(p0_b, p1_b, p2_b, p3_b, num_points=60)
        len2 = calculate_bezier_length(pts2)

        return (pts1, pts2, len1, len2)

    def render_back_accessories(
        self,
        character: StickmanCharacter,
        pose: StickmanPose,
        canvas_position: Point2D,
        facing: int = 1,
        canvas_size: tuple[int, int] = HumanoidBodyRenderer.DEFAULT_CANVAS_SIZE,
    ) -> Image.Image:
        """
        Render accessories that lie BEHIND the humanoid body.

        Elements:
          - Dark Wukong: Tattered Crimson Scarf / Cape + Twin Pheasant Plumes.
          - Erlang Shen: Silver-Slate Warrior Cloak.
          - Celestial General: Crimson General Cloak.
        """
        if facing not in (+1, -1):
            raise ValueError(f"Facing must be +1 or -1, got {facing}")
        scale = character.scale
        if scale <= 0.1 or scale > 5.0 or not math.isfinite(scale):
            raise ValueError(f"scale must be in range (0.1, 5.0], got {scale}")

        width, height = canvas_size
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        joints = self._body_renderer.transform_joints(
            pose=pose,
            canvas_position=canvas_position,
            facing=facing,
            scale=scale,
        )
        head_pt = joints[JointType.HEAD]
        neck_pt = joints[JointType.NECK]
        chest_pt = joints[JointType.CHEST]
        flow_dir = -facing

        skin = character.skin

        if skin == CharacterSkin.DARK_WUKONG:
            # 1. Tattered Crimson Scarf / Cape (Khăn choàng rách)
            # Anchored around neck and chest, flows opposite to facing
            scarf_origin_x = neck_pt.x + (2.0 * facing * scale)
            scarf_origin_y = neck_pt.y - (4.0 * scale)

            # Tattered ragged tail points (deterministic natural cuts)
            tattered_scarf_poly = [
                (scarf_origin_x, scarf_origin_y),
                (neck_pt.x + (15.0 * flow_dir * scale), neck_pt.y - (2.0 * scale)),
                (neck_pt.x + (50.0 * flow_dir * scale), neck_pt.y + (12.0 * scale)),
                (neck_pt.x + (85.0 * flow_dir * scale), neck_pt.y + (20.0 * scale)),
                (neck_pt.x + (70.0 * flow_dir * scale), neck_pt.y + (32.0 * scale)),
                (neck_pt.x + (95.0 * flow_dir * scale), neck_pt.y + (48.0 * scale)),
                (neck_pt.x + (65.0 * flow_dir * scale), neck_pt.y + (60.0 * scale)),
                (neck_pt.x + (80.0 * flow_dir * scale), neck_pt.y + (75.0 * scale)),
                (neck_pt.x + (45.0 * flow_dir * scale), neck_pt.y + (85.0 * scale)),
                (chest_pt.x + (8.0 * flow_dir * scale), chest_pt.y + (10.0 * scale)),
                (neck_pt.x, neck_pt.y + (6.0 * scale)),
            ]
            # Deep crimson base
            draw.polygon(tattered_scarf_poly, fill=(178, 34, 34, 255))
            # Dark fold lines for fabric depth
            draw.line(
                [
                    (neck_pt.x + (15.0 * flow_dir * scale), neck_pt.y),
                    (neck_pt.x + (70.0 * flow_dir * scale), neck_pt.y + (32.0 * scale)),
                ],
                fill=(115, 18, 18, 255),
                width=max(1, round(2.0 * scale)),
            )
            draw.line(
                [
                    (neck_pt.x + (30.0 * flow_dir * scale), neck_pt.y + (10.0 * scale)),
                    (neck_pt.x + (65.0 * flow_dir * scale), neck_pt.y + (60.0 * scale)),
                ],
                fill=(115, 18, 18, 255),
                width=max(1, round(2.0 * scale)),
            )

            # 2. Twin Pheasant Plumes (2 sợi lông chim trĩ ~180px)
            pts1, pts2, _, _ = self.get_feather_bezier_curves(head_pt, facing, scale)
            feather_color = (230, 184, 0, 255)  # Radiant amber gold
            feather_tip_color = (60, 45, 10, 255)  # Dark ink tip

            # Plume 1: Base curve + dark tip
            split_idx = int(len(pts1) * 0.85)
            draw.line(pts1[:split_idx + 1], fill=feather_color, width=max(2, round(3.0 * scale)))
            draw.line(pts1[split_idx:], fill=feather_tip_color, width=max(1, round(2.0 * scale)))

            # Plume 2: Inner curve + dark tip
            split_idx_b = int(len(pts2) * 0.85)
            draw.line(pts2[:split_idx_b + 1], fill=feather_color, width=max(2, round(2.5 * scale)))
            draw.line(pts2[split_idx_b:], fill=feather_tip_color, width=max(1, round(1.8 * scale)))

        elif skin == CharacterSkin.ERLANG_SHEN:
            # Silver-slate warrior cloak flowing behind shoulders
            sh_l = joints[JointType.SHOULDER_L]
            sh_r = joints[JointType.SHOULDER_R]
            cloak_top_x = (sh_l.x + sh_r.x) / 2.0
            cloak_top_y = neck_pt.y

            cloak_poly = [
                (cloak_top_x + (5.0 * facing * scale), cloak_top_y),
                (cloak_top_x + (40.0 * flow_dir * scale), cloak_top_y + (20.0 * scale)),
                (cloak_top_x + (85.0 * flow_dir * scale), cloak_top_y + (70.0 * scale)),
                (cloak_top_x + (90.0 * flow_dir * scale), cloak_top_y + (110.0 * scale)),
                (cloak_top_x + (60.0 * flow_dir * scale), cloak_top_y + (112.0 * scale)),
                (cloak_top_x + (30.0 * flow_dir * scale), cloak_top_y + (95.0 * scale)),
                (cloak_top_x - (5.0 * facing * scale), cloak_top_y + (30.0 * scale)),
            ]
            draw.polygon(cloak_poly, fill=(226, 232, 240, 255), outline=(160, 174, 192, 255))
            # Cloak shadow fold
            draw.line(
                [
                    (cloak_top_x + (25.0 * flow_dir * scale), cloak_top_y + (15.0 * scale)),
                    (cloak_top_x + (60.0 * flow_dir * scale), cloak_top_y + (110.0 * scale)),
                ],
                fill=(160, 174, 192, 255),
                width=max(1, round(2.0 * scale)),
            )

        elif skin == CharacterSkin.CELESTIAL_GENERAL:
            # Crimson warrior general cape
            cloak_poly = [
                (neck_pt.x + (5.0 * facing * scale), neck_pt.y),
                (neck_pt.x + (45.0 * flow_dir * scale), neck_pt.y + (25.0 * scale)),
                (neck_pt.x + (90.0 * flow_dir * scale), neck_pt.y + (85.0 * scale)),
                (neck_pt.x + (70.0 * flow_dir * scale), neck_pt.y + (125.0 * scale)),
                (neck_pt.x + (35.0 * flow_dir * scale), neck_pt.y + (115.0 * scale)),
                (chest_pt.x, chest_pt.y + (20.0 * scale)),
            ]
            draw.polygon(cloak_poly, fill=(197, 48, 48, 255), outline=(155, 44, 44, 255))

        return img

    def render_front_accessories(
        self,
        character: StickmanCharacter,
        pose: StickmanPose,
        canvas_position: Point2D,
        facing: int = 1,
        canvas_size: tuple[int, int] = HumanoidBodyRenderer.DEFAULT_CANVAS_SIZE,
    ) -> Image.Image:
        """
        Render accessories that lie IN FRONT OF the humanoid body and face.

        Elements:
          - Dark Wukong: Vòng Kim Cô (Broken V-notch Golden Headband).
          - Erlang Shen: Spiked Silver Warrior Helmet + Angular Shoulder Pauldrons.
          - Celestial General: General Helmet with Red Plume Tassel + Heavy Pauldrons.
          - Celestial Soldier: Conical Soldier Helmet with Short Tassel + Simple Pauldrons.
        """
        if facing not in (+1, -1):
            raise ValueError(f"Facing must be +1 or -1, got {facing}")
        scale = character.scale
        if scale <= 0.1 or scale > 5.0 or not math.isfinite(scale):
            raise ValueError(f"scale must be in range (0.1, 5.0], got {scale}")

        width, height = canvas_size
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        joints = self._body_renderer.transform_joints(
            pose=pose,
            canvas_position=canvas_position,
            facing=facing,
            scale=scale,
        )
        head_pt = joints[JointType.HEAD]
        sh_l = joints[JointType.SHOULDER_L]
        sh_r = joints[JointType.SHOULDER_R]
        flow_dir = -facing

        skin = character.skin

        if skin == CharacterSkin.DARK_WUKONG:
            # 1. Vòng Kim Cô gãy nát chữ V (Broken V-notch Golden Headband)
            # Sits on forehead contour, strictly ABOVE eyes (Y <= head_pt.y - 8*scale)
            v_apex = (head_pt.x + (23.0 * facing * scale), head_pt.y - (8.0 * scale))
            v_left = (head_pt.x + (16.0 * facing * scale), head_pt.y - (17.0 * scale))
            v_right = (head_pt.x + (22.0 * facing * scale), head_pt.y - (19.0 * scale))
            crown = (head_pt.x - (4.0 * facing * scale), head_pt.y - (25.0 * scale))
            back = (head_pt.x - (22.0 * facing * scale), head_pt.y - (12.0 * scale))

            gold_band_pts = [back, crown, v_left, v_apex, v_right]
            draw.line(
                gold_band_pts,
                fill=(255, 215, 0, 255),  # Radiant gold
                width=max(2, round(3.0 * scale)),
            )
            # Center forehead V-jewel bead
            bead_r = max(1.5, 2.5 * scale)
            draw.ellipse(
                [
                    v_apex[0] - bead_r,
                    v_apex[1] - bead_r,
                    v_apex[0] + bead_r,
                    v_apex[1] + bead_r,
                ],
                fill=(255, 240, 150, 255),
            )

        elif skin == CharacterSkin.ERLANG_SHEN:
            # 1. Mũ chiến thần có chóp nhọn (Spiked Silver Warrior Helmet)
            # Tall pointed crest; brow arches up cleanly above the Third Eye
            crest_spike = (head_pt.x + (2.0 * facing * scale), head_pt.y - (46.0 * scale))
            front_brow = (head_pt.x + (20.0 * facing * scale), head_pt.y - (14.0 * scale))
            mid_brow = (head_pt.x + (6.0 * facing * scale), head_pt.y - (18.0 * scale))
            rear_brow = (head_pt.x - (12.0 * facing * scale), head_pt.y - (18.0 * scale))
            back_rim = (head_pt.x - (24.0 * facing * scale), head_pt.y - (6.0 * scale))
            rear_fin = (head_pt.x - (16.0 * facing * scale), head_pt.y - (28.0 * scale))

            helmet_poly = [
                crest_spike,
                front_brow,
                mid_brow,
                rear_brow,
                back_rim,
                rear_fin,
            ]
            draw.polygon(helmet_poly, fill=(226, 232, 240, 255), outline=(74, 85, 104, 255))
            # Helmet central ridge line
            draw.line(
                [crest_spike, mid_brow],
                fill=(160, 174, 192, 255),
                width=max(1, round(2.0 * scale)),
            )

            # 2. Giáp vai hai bên (Angular Shoulder Pauldrons)
            for sh_pt, side_sign in ((sh_l, -1), (sh_r, 1)):
                tip = (sh_pt.x + (15.0 * side_sign * scale), sh_pt.y - (15.0 * scale))
                outer = (sh_pt.x + (18.0 * side_sign * scale), sh_pt.y + (4.0 * scale))
                inner = (sh_pt.x - (4.0 * side_sign * scale), sh_pt.y + (2.0 * scale))
                base = (sh_pt.x, sh_pt.y - (6.0 * scale))
                draw.polygon(
                    [base, tip, outer, inner],
                    fill=(203, 213, 224, 255),
                    outline=(74, 85, 104, 255),
                )

        elif skin == CharacterSkin.CELESTIAL_GENERAL:
            # 1. Celestial General Helmet
            helm_mount = (head_pt.x, head_pt.y - (34.0 * scale))
            helm_poly = [
                helm_mount,
                (head_pt.x + (18.0 * facing * scale), head_pt.y - (14.0 * scale)),
                (head_pt.x + (8.0 * facing * scale), head_pt.y - (18.0 * scale)),
                (head_pt.x - (14.0 * facing * scale), head_pt.y - (18.0 * scale)),
                (head_pt.x - (22.0 * facing * scale), head_pt.y - (10.0 * scale)),
            ]
            draw.polygon(helm_poly, fill=(203, 213, 224, 255), outline=(45, 55, 72, 255))

            # 2. Chùm tua đỏ trên đỉnh mũ (Red Plume Tassel)
            tassel_p0 = helm_mount
            tassel_p1 = (helm_mount[0] + (10.0 * flow_dir * scale), helm_mount[1] - (8.0 * scale))
            tassel_p2 = (helm_mount[0] + (25.0 * flow_dir * scale), helm_mount[1] + (2.0 * scale))
            tassel_p3 = (helm_mount[0] + (32.0 * flow_dir * scale), helm_mount[1] + (16.0 * scale))
            tassel_pts = evaluate_cubic_bezier(tassel_p0, tassel_p1, tassel_p2, tassel_p3, num_points=30)
            draw.line(tassel_pts, fill=(229, 62, 62, 255), width=max(2, round(4.0 * scale)))

            # 3. Heavy General Shoulder Pauldrons
            for sh_pt, side_sign in ((sh_l, -1), (sh_r, 1)):
                tip = (sh_pt.x + (18.0 * side_sign * scale), sh_pt.y - (18.0 * scale))
                outer = (sh_pt.x + (22.0 * side_sign * scale), sh_pt.y + (6.0 * scale))
                inner = (sh_pt.x - (5.0 * side_sign * scale), sh_pt.y + (3.0 * scale))
                base = (sh_pt.x, sh_pt.y - (8.0 * scale))
                draw.polygon(
                    [base, tip, outer, inner],
                    fill=(203, 213, 224, 255),
                    outline=(45, 55, 72, 255),
                )

        elif skin == CharacterSkin.CELESTIAL_SOLDIER_SQUAD:
            # 1. Celestial Soldier Conical Kettle Helmet
            helm_mount = (head_pt.x, head_pt.y - (30.0 * scale))
            helm_poly = [
                helm_mount,
                (head_pt.x + (16.0 * facing * scale), head_pt.y - (12.0 * scale)),
                (head_pt.x - (16.0 * facing * scale), head_pt.y - (12.0 * scale)),
            ]
            draw.polygon(helm_poly, fill=(160, 174, 192, 255), outline=(45, 55, 72, 255))

            # 2. Shorter Red Tassel
            tassel_p0 = helm_mount
            tassel_p1 = (helm_mount[0] + (6.0 * flow_dir * scale), helm_mount[1] - (4.0 * scale))
            tassel_p2 = (helm_mount[0] + (14.0 * flow_dir * scale), helm_mount[1] + (2.0 * scale))
            tassel_p3 = (helm_mount[0] + (18.0 * flow_dir * scale), helm_mount[1] + (10.0 * scale))
            tassel_pts = evaluate_cubic_bezier(tassel_p0, tassel_p1, tassel_p2, tassel_p3, num_points=20)
            draw.line(tassel_pts, fill=(229, 62, 62, 255), width=max(1, round(2.5 * scale)))

            # 3. Simple Soldier Shoulder Caps
            for sh_pt, side_sign in ((sh_l, -1), (sh_r, 1)):
                cap_r = max(4.0, 7.0 * scale)
                draw.ellipse(
                    [
                        sh_pt.x - cap_r,
                        sh_pt.y - cap_r,
                        sh_pt.x + cap_r,
                        sh_pt.y + cap_r,
                    ],
                    fill=(160, 174, 192, 255),
                    outline=(45, 55, 72, 255),
                )

        return img


@dataclass(frozen=True)
class GripValidationResult:
    """Detailed audit report of weapon grip geometry and alignment."""

    is_valid: bool
    pose_name: str
    weapon_type: WeaponType
    weapon_anchor: JointType
    secondary_grip: Optional[JointType]
    anchor_canvas: Point2D
    secondary_canvas: Optional[Point2D]
    weapon_angle_deg: float
    wrist_to_wrist_angle_deg: Optional[float]
    d_perp: float
    d_parallel: float
    shaft_length: float
    message: str


class WeaponRenderer:
    """
    Renders Dark Myth stickman weapons on a transparent RGBA canvas (G5.2.3.3).

    Supported Weapons:
      - RUYI_STAFF: Black ink staff with ruby-inlaid gold箍 caps at both ends (nominal 340px).
      - THREE_POINTED_SPEAR: Tempered steel spear with trident three-pointed blade and collar (nominal 360px).
      - CELESTIAL_HALBERD: Ancient Chinese halberd with side crescent blade and red tassel (nominal 320px).
      - UNARMED: Clean transparent canvas (alpha = 0).
      - GIANT_GOLDEN_PALM: Dispatches/delegates to Buddha Palm engine (G5.2.3.4), transparent here.

    Coordinate & Grip Contract:
      - Primary Grip: Anchored at PoseDefinition.weapon_anchor (default WRIST_R).
      - Secondary Grip: Validated at PoseDefinition.secondary_grip (default WRIST_L).
      - Facing +1: weapon_angle_deg preserved.
      - Facing -1: weapon_angle_deg reflected via 180° - theta.
      - Scale: 0.8, 1.0, 1.25 scales length, thickness and ornamentation proportionally.
      - Two-handed alignment: Can align axis along vector connecting wrists or nominal angle.
    """

    DEFAULT_CANVAS_SIZE: tuple[int, int] = (1080, 1920)

    # Nominal lengths at scale 1.0
    LENGTH_RUYI_STAFF: float = 340.0
    LENGTH_THREE_POINTED_SPEAR: float = 360.0
    LENGTH_CELESTIAL_HALBERD: float = 320.0

    # Perpendicular grip tolerance (px at scale 1.0)
    MAX_PERP_TOLERANCE_PX: float = 18.0

    def __init__(
        self,
        body_renderer: Optional[HumanoidBodyRenderer] = None,
        buddha_palm_renderer: Optional[BuddhaPalmRenderer] = None,
    ) -> None:
        self._body_renderer = body_renderer or HumanoidBodyRenderer()
        self._buddha_palm_renderer = buddha_palm_renderer or BuddhaPalmRenderer()

    def get_buddha_palm_renderer(self) -> BuddhaPalmRenderer:
        """Return attached BuddhaPalmRenderer instance."""
        return self._buddha_palm_renderer

    def get_weapon_length(self, weapon_type: WeaponType, scale: float = 1.0) -> float:
        """Return total nominal length of weapon scaled proportionally."""
        if weapon_type == WeaponType.RUYI_STAFF:
            return self.LENGTH_RUYI_STAFF * scale
        elif weapon_type == WeaponType.THREE_POINTED_SPEAR:
            return self.LENGTH_THREE_POINTED_SPEAR * scale
        elif weapon_type == WeaponType.CELESTIAL_HALBERD:
            return self.LENGTH_CELESTIAL_HALBERD * scale
        return 0.0

    def get_grip_distribution(
        self,
        weapon_type: WeaponType,
        pose_name: str,
        scale: float = 1.0,
        ground_y: float = 1420.0,
        anchor_y: Optional[float] = None,
        u_y: Optional[float] = None,
    ) -> tuple[float, float]:
        """
        Return (tail_dist, tip_dist) relative to primary anchor.
        tail_dist + tip_dist == total_length.

        For standoff_idle (DEF-01):
          Computes reach_ground so that the planted tip rests on ground_y (1420.0)
          without penetrating it (max pixel Y <= 1421), while keeping total nominal
          weapon length intact by shifting hand placement upward.
        """
        total_len = self.get_weapon_length(weapon_type, scale)
        if total_len <= 0.0:
            return 0.0, 0.0

        if pose_name == "combat_stance":
            tail_dist = min(total_len * 0.70, 220.0 * scale)
        elif pose_name == "overhead_slam":
            tail_dist = min(total_len * 0.35, 90.0 * scale)
        elif pose_name == "guard_block":
            tail_dist = min(total_len * 0.50, 160.0 * scale)
        elif pose_name == "vortex_sweep":
            tail_dist = total_len * 0.50
        elif pose_name == "forward_charge":
            tail_dist = min(total_len * 0.45, 140.0 * scale)
        elif pose_name == "knockback_slide":
            tail_dist = min(total_len * 0.35, 100.0 * scale)
        elif pose_name == "standoff_idle":
            # DEF-01: Planted weapon in standoff_idle rests precisely on ground plane
            if anchor_y is not None and u_y is not None and u_y > 1e-4:
                reach_ground = (ground_y - anchor_y) / u_y
            else:
                reach_ground = 137.0825 * scale
            tip_dist = min(total_len * 0.85, max(total_len * 0.15, reach_ground))
            tail_dist = total_len - tip_dist
            return tail_dist, tip_dist
        else:
            tail_dist = min(total_len * 0.45, 140.0 * scale)

        tip_dist = total_len - tail_dist
        return tail_dist, tip_dist

    def validate_grip(
        self,
        character: StickmanCharacter,
        pose: StickmanPose,
        canvas_position: Point2D,
        facing: int = 1,
        pose_def: Optional[PoseDefinition] = None,
        tolerance_perp: float = MAX_PERP_TOLERANCE_PX,
        align_two_hands: Optional[bool] = None,
    ) -> GripValidationResult:
        """
        Validate perpendicular and parallel grip geometry against weapon axis contract.

        Checks:
          - d_perp <= tolerance_perp * scale (default 18.0 px at scale 1.0).
          - secondary grip lies within graspable shaft range [-tail_dist, tip_dist].
        """
        pdef = pose_def
        if pdef is None:
            try:
                pdef = PoseCatalog.get_definition(pose.name)
            except Exception:
                pdef = None

        resolved_align = (pdef is not None and pdef.secondary_grip is not None) if align_two_hands is None else bool(align_two_hands)

        joints = self._body_renderer.transform_joints(
            pose=pose,
            canvas_position=canvas_position,
            facing=facing,
            scale=character.scale,
        )

        anchor_joint = pdef.weapon_anchor if pdef else JointType.WRIST_R
        p_anchor = joints[anchor_joint]
        scale = character.scale
        total_len = self.get_weapon_length(character.weapon, scale)

        if pdef is None or pdef.secondary_grip is None:
            # Single-handed weapon grip
            local_ang = pdef.weapon_angle_deg if pdef else 0.0
            canvas_ang = local_ang if facing == 1 else (180.0 - local_ang)
            return GripValidationResult(
                is_valid=True,
                pose_name=pose.name,
                weapon_type=character.weapon,
                weapon_anchor=anchor_joint,
                secondary_grip=None,
                anchor_canvas=p_anchor,
                secondary_canvas=None,
                weapon_angle_deg=canvas_ang,
                wrist_to_wrist_angle_deg=None,
                d_perp=0.0,
                d_parallel=0.0,
                shaft_length=total_len,
                message="Single-handed grip valid: primary anchor precisely matched.",
            )

        sec_joint = pdef.secondary_grip
        p_sec = joints[sec_joint]

        # Calculate nominal or aligned axis
        if resolved_align:
            wrist_dist = math.hypot(p_anchor.x - p_sec.x, p_anchor.y - p_sec.y)
            if wrist_dist > 40.0 * scale:
                rad = math.atan2(p_anchor.y - p_sec.y, p_anchor.x - p_sec.x)
                ux, uy = math.cos(rad), math.sin(rad)
                d_perp = 0.0
                d_par = -wrist_dist
                anc_used = p_anchor
            else:
                rad = math.radians(pdef.weapon_angle_deg if facing == 1 else 180.0 - pdef.weapon_angle_deg)
                ux, uy = math.cos(rad), math.sin(rad)
                anc_used = Point2D((p_anchor.x + p_sec.x) / 2.0, (p_anchor.y + p_sec.y) / 2.0)
                vx, vy = p_sec.x - anc_used.x, p_sec.y - anc_used.y
                d_perp = abs(vx * uy - vy * ux)
                d_par = vx * ux + vy * uy
            canvas_ang = math.degrees(rad)
        else:
            rad = math.radians(pdef.weapon_angle_deg if facing == 1 else 180.0 - pdef.weapon_angle_deg)
            ux, uy = math.cos(rad), math.sin(rad)
            anc_used = p_anchor
            vx, vy = p_sec.x - p_anchor.x, p_sec.y - p_anchor.y
            d_par = vx * ux + vy * uy
            d_perp = abs(vx * uy - vy * ux)
            canvas_ang = math.degrees(rad)

        tail_dist, tip_dist = self.get_grip_distribution(
            character.weapon,
            pose.name,
            scale,
            anchor_y=anc_used.y,
            u_y=uy,
        )

        w2w_rad = math.atan2(p_anchor.y - p_sec.y, p_anchor.x - p_sec.x)
        w2w_deg = math.degrees(w2w_rad)

        tol = tolerance_perp * scale
        is_perp_ok = d_perp <= (tol + 1e-4)
        is_par_ok = (-tail_dist - 5.0 * scale) <= d_par <= (tip_dist + 5.0 * scale)

        is_valid = is_perp_ok and is_par_ok
        if not is_perp_ok:
            msg = (
                f"Perpendicular grip mismatch on '{pose.name}': d_perp={d_perp:.2f}px exceeds "
                f"tolerance={tol:.2f}px (nominal angle={canvas_ang:.1f}°, wrist-to-wrist={w2w_deg:.1f}°)."
            )
        elif not is_par_ok:
            msg = (
                f"Secondary grip along-axis projection d_parallel={d_par:.2f}px out of bounds "
                f"[-{tail_dist:.1f}, {tip_dist:.1f}] on '{pose.name}'."
            )
        else:
            msg = f"Two-handed grip valid on '{pose.name}': d_perp={d_perp:.2f}px <= {tol:.2f}px."

        return GripValidationResult(
            is_valid=is_valid,
            pose_name=pose.name,
            weapon_type=character.weapon,
            weapon_anchor=anchor_joint,
            secondary_grip=sec_joint,
            anchor_canvas=anc_used,
            secondary_canvas=p_sec,
            weapon_angle_deg=canvas_ang,
            wrist_to_wrist_angle_deg=w2w_deg,
            d_perp=d_perp,
            d_parallel=d_par,
            shaft_length=total_len,
            message=msg,
        )

    def get_weapon_endpoints(
        self,
        character: StickmanCharacter,
        pose: StickmanPose,
        canvas_position: Point2D,
        facing: int = 1,
        pose_def: Optional[PoseDefinition] = None,
        custom_angle_deg: Optional[float] = None,
        align_two_hands: Optional[bool] = None,
    ) -> tuple[Point2D, Point2D, Point2D, float]:
        """
        Compute (tail_pt, tip_pt, eff_anchor_pt, effective_canvas_angle_deg).
        """
        pdef = pose_def
        if pdef is None:
            try:
                pdef = PoseCatalog.get_definition(pose.name)
            except Exception:
                pdef = None

        resolved_align = (pdef is not None and pdef.secondary_grip is not None) if align_two_hands is None else bool(align_two_hands)

        joints = self._body_renderer.transform_joints(
            pose=pose,
            canvas_position=canvas_position,
            facing=facing,
            scale=character.scale,
        )
        anchor_joint = pdef.weapon_anchor if pdef else JointType.WRIST_R
        p_anchor = joints[anchor_joint]
        scale = character.scale

        if custom_angle_deg is not None:
            canvas_ang = custom_angle_deg if facing == 1 else (180.0 - custom_angle_deg)
            rad = math.radians(canvas_ang)
            u = (math.cos(rad), math.sin(rad))
            eff_anchor = p_anchor
        elif resolved_align and pdef and pdef.secondary_grip:
            p_sec = joints[pdef.secondary_grip]
            wrist_dist = math.hypot(p_anchor.x - p_sec.x, p_anchor.y - p_sec.y)
            if wrist_dist > 40.0 * scale:
                rad = math.atan2(p_anchor.y - p_sec.y, p_anchor.x - p_sec.x)
                u = (math.cos(rad), math.sin(rad))
                eff_anchor = p_anchor
            else:
                rad = math.radians(pdef.weapon_angle_deg if facing == 1 else 180.0 - pdef.weapon_angle_deg)
                u = (math.cos(rad), math.sin(rad))
                eff_anchor = Point2D((p_anchor.x + p_sec.x) / 2.0, (p_anchor.y + p_sec.y) / 2.0)
            canvas_ang = math.degrees(rad)
        else:
            local_ang = pdef.weapon_angle_deg if pdef else 0.0
            canvas_ang = local_ang if facing == 1 else (180.0 - local_ang)
            rad = math.radians(canvas_ang)
            u = (math.cos(rad), math.sin(rad))
            eff_anchor = p_anchor

        tail_dist, tip_dist = self.get_grip_distribution(
            character.weapon,
            pose.name,
            scale,
            anchor_y=eff_anchor.y,
            u_y=u[1],
        )
        tail_pt = Point2D(eff_anchor.x - u[0] * tail_dist, eff_anchor.y - u[1] * tail_dist)
        tip_pt = Point2D(eff_anchor.x + u[0] * tip_dist, eff_anchor.y + u[1] * tip_dist)

        return (tail_pt, tip_pt, eff_anchor, canvas_ang)

    def render_weapon(
        self,
        character: StickmanCharacter,
        pose: StickmanPose,
        canvas_position: Point2D,
        facing: int = 1,
        canvas_size: tuple[int, int] = DEFAULT_CANVAS_SIZE,
        pose_def: Optional[PoseDefinition] = None,
        custom_angle_deg: Optional[float] = None,
        align_two_hands: Optional[bool] = None,
        delegate_buddha_palm: bool = False,
        palm_position: Optional[Point2D] = None,
        palm_scale: Optional[float] = None,
        palm_direction: str = "down",
        palm_descent_progress: float = 1.0,
    ) -> Image.Image:
        """
        Render the character's weapon as an independent transparent RGBA layer.

        For GIANT_GOLDEN_PALM:
          - If delegate_buddha_palm=False (default): returns transparent layer (contract compliant with test_05).
          - If delegate_buddha_palm=True: dispatches rendering to attached BuddhaPalmRenderer.
        """
        if facing not in (+1, -1):
            raise ValueError(f"Facing must be +1 or -1, got {facing}")
        scale = character.scale
        if scale <= 0.1 or scale > 5.0 or not math.isfinite(scale):
            raise ValueError(f"scale must be in range (0.1, 5.0], got {scale}")
        if not (math.isfinite(canvas_position.x) and math.isfinite(canvas_position.y)):
            raise ValueError(f"canvas_position must have finite coordinates, got {canvas_position}")

        width, height = canvas_size
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        # Check unarmed or special Buddha palm
        if character.weapon == WeaponType.UNARMED:
            return img

        if character.weapon == WeaponType.GIANT_GOLDEN_PALM:
            if delegate_buddha_palm:
                p_pos = palm_position or canvas_position
                p_scale = palm_scale if palm_scale is not None else (character.scale * 3.5 if character.scale <= 1.5 else character.scale)
                return self._buddha_palm_renderer.render_palm(
                    position=p_pos,
                    scale=p_scale,
                    facing=facing,
                    direction=palm_direction,
                    descent_progress=palm_descent_progress,
                    canvas_size=canvas_size,
                )
            logger.info("GIANT_GOLDEN_PALM belongs to BuddhaPalmRenderer (G5.2.3.4), transparent here.")
            return img

        tail_pt, tip_pt, eff_anchor, _ = self.get_weapon_endpoints(
            character=character,
            pose=pose,
            canvas_position=canvas_position,
            facing=facing,
            pose_def=pose_def,
            custom_angle_deg=custom_angle_deg,
            align_two_hands=align_two_hands,
        )

        dx = tip_pt.x - tail_pt.x
        dy = tip_pt.y - tail_pt.y
        total_len = math.hypot(dx, dy)
        if total_len <= 1e-4:
            return img

        u = (dx / total_len, dy / total_len)
        n = (-u[1], u[0])

        draw = ImageDraw.Draw(img)

        if character.weapon == WeaponType.RUYI_STAFF:
            self._render_ruyi_staff(draw, tail_pt, tip_pt, u, n, scale)
        elif character.weapon == WeaponType.THREE_POINTED_SPEAR:
            self._render_three_pointed_spear(draw, tail_pt, tip_pt, u, n, scale)
        elif character.weapon == WeaponType.CELESTIAL_HALBERD:
            self._render_celestial_halberd(draw, tail_pt, tip_pt, u, n, scale, facing)

        return img

    def _render_ruyi_staff(
        self,
        draw: ImageDraw.ImageDraw,
        tail_pt: Point2D,
        tip_pt: Point2D,
        u: tuple[float, float],
        n: tuple[float, float],
        scale: float,
    ) -> None:
        """Render Dark Wukong's Ruyi Staff (Thiết Bảng Như Ý)."""
        w = max(2.0, 6.0 * scale)
        w_cap = max(3.0, 8.5 * scale)
        cap_len = 40.0 * scale

        # 1. Main Black/Ink Staff Body
        poly_shaft = [
            (tail_pt.x - n[0] * w / 2.0, tail_pt.y - n[1] * w / 2.0),
            (tip_pt.x - n[0] * w / 2.0, tip_pt.y - n[1] * w / 2.0),
            (tip_pt.x + n[0] * w / 2.0, tip_pt.y + n[1] * w / 2.0),
            (tail_pt.x + n[0] * w / 2.0, tail_pt.y + n[1] * w / 2.0),
        ]
        draw.polygon(poly_shaft, fill=(20, 20, 22, 255), outline=(161, 18, 18, 255))

        # Red accent core stroke
        draw.line(
            [(tail_pt.x, tail_pt.y), (tip_pt.x, tip_pt.y)],
            fill=(180, 20, 20, 255),
            width=max(1, round(1.5 * scale)),
        )

        # 2. Golden箍 Caps at both ends (Tail & Tip)
        for p_end, dir_sign in [(tail_pt, 1.0), (tip_pt, -1.0)]:
            p_cap_inner = (p_end.x + dir_sign * u[0] * cap_len, p_end.y + dir_sign * u[1] * cap_len)
            poly_cap = [
                (p_end.x - n[0] * w_cap / 2.0, p_end.y - n[1] * w_cap / 2.0),
                (p_cap_inner[0] - n[0] * w_cap / 2.0, p_cap_inner[1] - n[1] * w_cap / 2.0),
                (p_cap_inner[0] + n[0] * w_cap / 2.0, p_cap_inner[1] + n[1] * w_cap / 2.0),
                (p_end.x + n[0] * w_cap / 2.0, p_end.y + n[1] * w_cap / 2.0),
            ]
            draw.polygon(poly_cap, fill=(230, 184, 0, 255), outline=(184, 134, 11, 255))

            # Ruby/crimson inlaid ring in center of gold cap
            p_r1 = (p_end.x + dir_sign * u[0] * cap_len * 0.38, p_end.y + dir_sign * u[1] * cap_len * 0.38)
            p_r2 = (p_end.x + dir_sign * u[0] * cap_len * 0.62, p_end.y + dir_sign * u[1] * cap_len * 0.62)
            poly_ruby = [
                (p_r1[0] - n[0] * w_cap / 2.0, p_r1[1] - n[1] * w_cap / 2.0),
                (p_r2[0] - n[0] * w_cap / 2.0, p_r2[1] - n[1] * w_cap / 2.0),
                (p_r2[0] + n[0] * w_cap / 2.0, p_r2[1] + n[1] * w_cap / 2.0),
                (p_r1[0] + n[0] * w_cap / 2.0, p_r1[1] + n[1] * w_cap / 2.0),
            ]
            draw.polygon(poly_ruby, fill=(217, 38, 38, 255))

    def _render_three_pointed_spear(
        self,
        draw: ImageDraw.ImageDraw,
        tail_pt: Point2D,
        tip_pt: Point2D,
        u: tuple[float, float],
        n: tuple[float, float],
        scale: float,
    ) -> None:
        """Render Erlang Shen's Three Pointed Spear (Tam Tiêm Lưỡng Nhận Đao)."""
        w = max(2.0, 5.0 * scale)
        head_len = 65.0 * scale
        p_collar = (tip_pt.x - u[0] * head_len, tip_pt.y - u[1] * head_len)

        # 1. Main Tempered Steel Shaft
        poly_shaft = [
            (tail_pt.x - n[0] * w / 2.0, tail_pt.y - n[1] * w / 2.0),
            (p_collar[0] - n[0] * w / 2.0, p_collar[1] - n[1] * w / 2.0),
            (p_collar[0] + n[0] * w / 2.0, p_collar[1] + n[1] * w / 2.0),
            (tail_pt.x + n[0] * w / 2.0, tail_pt.y + n[0] * w / 2.0),
        ]
        draw.polygon(poly_shaft, fill=(45, 55, 72, 255), outline=(30, 38, 50, 255))

        # 2. Golden Lotus Collar
        w_col = max(3.0, 8.5 * scale)
        p_col_top = (p_collar[0] + u[0] * 8.0 * scale, p_collar[1] + u[1] * 8.0 * scale)
        poly_col = [
            (p_collar[0] - n[0] * w_col / 2.0, p_collar[1] - n[1] * w_col / 2.0),
            (p_col_top[0] - n[0] * w_col / 2.0, p_col_top[1] - n[1] * w_col / 2.0),
            (p_col_top[0] + n[0] * w_col / 2.0, p_col_top[1] + n[1] * w_col / 2.0),
            (p_collar[0] + n[0] * w_col / 2.0, p_collar[1] + n[1] * w_col / 2.0),
        ]
        draw.polygon(poly_col, fill=(230, 184, 0, 255), outline=(184, 134, 11, 255))

        # 3. Central Main Blade (Diamond leaf spearhead)
        blade_len = 57.0 * scale
        w_b = 6.5 * scale
        p_mid = (p_col_top[0] + u[0] * blade_len * 0.35, p_col_top[1] + u[1] * blade_len * 0.35)
        poly_blade = [
            p_col_top,
            (p_mid[0] - n[0] * w_b, p_mid[1] - n[1] * w_b),
            (tip_pt.x, tip_pt.y),
            (p_mid[0] + n[0] * w_b, p_mid[1] + n[1] * w_b),
        ]
        draw.polygon(poly_blade, fill=(226, 232, 240, 255), outline=(45, 55, 72, 255))
        draw.line([p_col_top, (tip_pt.x, tip_pt.y)], fill=(255, 255, 255, 255), width=max(1, round(1.5 * scale)))

        # 4. Two Symmetrical Side Prongs (Trident Points)
        side_spread = 15.0 * scale
        prong_reach = 33.0 * scale
        for side_sign in [-1.0, 1.0]:
            p_base = (p_col_top[0] + side_sign * n[0] * 3.0 * scale, p_col_top[1] + side_sign * n[1] * 3.0 * scale)
            p_out = (
                p_base[0] + side_sign * n[0] * side_spread + u[0] * 8.0 * scale,
                p_base[1] + side_sign * n[1] * side_spread + u[1] * 8.0 * scale,
            )
            p_prong_tip = (
                p_col_top[0] + side_sign * n[0] * (side_spread - 2.0 * scale) + u[0] * prong_reach,
                p_col_top[1] + side_sign * n[1] * (side_spread - 2.0 * scale) + u[1] * prong_reach,
            )
            p_inner = (
                p_col_top[0] + side_sign * n[0] * (side_spread - 5.0 * scale) + u[0] * 12.0 * scale,
                p_col_top[1] + side_sign * n[1] * (side_spread - 5.0 * scale) + u[1] * 12.0 * scale,
            )
            poly_prong = [p_base, p_out, p_prong_tip, p_inner]
            draw.polygon(poly_prong, fill=(226, 232, 240, 255), outline=(45, 55, 72, 255))

        # 5. Tail Conical Butt Spike
        p_tail_spike = (tail_pt.x - u[0] * 16.0 * scale, tail_pt.y - u[1] * 16.0 * scale)
        poly_spike = [
            (tail_pt.x - n[0] * w / 2.0, tail_pt.y - n[1] * w / 2.0),
            p_tail_spike,
            (tail_pt.x + n[0] * w / 2.0, tail_pt.y + n[1] * w / 2.0),
        ]
        draw.polygon(poly_spike, fill=(113, 128, 150, 255), outline=(45, 55, 72, 255))

    def _render_celestial_halberd(
        self,
        draw: ImageDraw.ImageDraw,
        tail_pt: Point2D,
        tip_pt: Point2D,
        u: tuple[float, float],
        n: tuple[float, float],
        scale: float,
        facing: int,
    ) -> None:
        """Render Celestial Halberd (Thiên Binh Đại Kích)."""
        w = max(2.0, 5.0 * scale)
        head_len = 55.0 * scale
        p_collar = (tip_pt.x - u[0] * head_len, tip_pt.y - u[1] * head_len)

        # 1. Main Dark Iron Shaft
        poly_shaft = [
            (tail_pt.x - n[0] * w / 2.0, tail_pt.y - n[1] * w / 2.0),
            (p_collar[0] - n[0] * w / 2.0, p_collar[1] - n[1] * w / 2.0),
            (p_collar[0] + n[0] * w / 2.0, p_collar[1] + n[1] * w / 2.0),
            (tail_pt.x + n[0] * w / 2.0, tail_pt.y + n[1] * w / 2.0),
        ]
        draw.polygon(poly_shaft, fill=(26, 32, 44, 255), outline=(15, 20, 25, 255))

        # 2. Golden Collar
        w_col = max(3.0, 8.0 * scale)
        p_col_top = (p_collar[0] + u[0] * 8.0 * scale, p_collar[1] + u[1] * 8.0 * scale)
        poly_col = [
            (p_collar[0] - n[0] * w_col / 2.0, p_collar[1] - n[1] * w_col / 2.0),
            (p_col_top[0] - n[0] * w_col / 2.0, p_col_top[1] - n[1] * w_col / 2.0),
            (p_col_top[0] + n[0] * w_col / 2.0, p_col_top[1] + n[1] * w_col / 2.0),
            (p_collar[0] + n[0] * w_col / 2.0, p_collar[1] + n[1] * w_col / 2.0),
        ]
        draw.polygon(poly_col, fill=(214, 158, 46, 255), outline=(184, 134, 11, 255))

        # 3. Crimson Tassel below collar
        tassel_dir = (-u[0], -u[1])
        for t_offset, t_len in [(-2.0, 22.0), (0.0, 26.0), (2.0, 20.0)]:
            p_t_start = (p_collar[0] + n[0] * t_offset * scale, p_collar[1] + n[1] * t_offset * scale)
            p_t_end = (
                p_t_start[0] + tassel_dir[0] * t_len * scale + n[0] * t_offset * 1.5 * scale,
                p_t_start[1] + tassel_dir[1] * t_len * scale + n[1] * t_offset * 1.5 * scale,
            )
            draw.line([p_t_start, p_t_end], fill=(197, 48, 48, 255), width=max(1, round(2.0 * scale)))

        # 4. Central Lance Blade
        w_blade = 5.0 * scale
        poly_lance = [
            (p_col_top[0] - n[0] * w_blade, p_col_top[1] - n[1] * w_blade),
            (tip_pt.x, tip_pt.y),
            (p_col_top[0] + n[0] * w_blade, p_col_top[1] + n[1] * w_blade),
        ]
        draw.polygon(poly_lance, fill=(203, 213, 224, 255), outline=(45, 55, 72, 255))
        draw.line([p_col_top, (tip_pt.x, tip_pt.y)], fill=(255, 255, 255, 255), width=max(1, round(1.2 * scale)))

        # 5. Side Crescent Blade (Phương Thiên Nguyệt Nha Đao)
        crescent_side = 1.0 * facing
        p_cross_low = (p_col_top[0] + u[0] * 8.0 * scale, p_col_top[1] + u[1] * 8.0 * scale)
        p_cross_high = (p_col_top[0] + u[0] * 28.0 * scale, p_col_top[1] + u[1] * 28.0 * scale)
        p_bar1_end = (
            p_cross_low[0] + crescent_side * n[0] * 14.0 * scale,
            p_cross_low[1] + crescent_side * n[1] * 14.0 * scale,
        )
        p_bar2_end = (
            p_cross_high[0] + crescent_side * n[0] * 14.0 * scale,
            p_cross_high[1] + crescent_side * n[1] * 14.0 * scale,
        )
        draw.line([p_cross_low, p_bar1_end], fill=(214, 158, 46, 255), width=max(1, round(2.5 * scale)))
        draw.line([p_cross_high, p_bar2_end], fill=(214, 158, 46, 255), width=max(1, round(2.5 * scale)))

        p_crescent_bot = (
            p_col_top[0] + u[0] * 2.0 * scale + crescent_side * n[0] * 12.0 * scale,
            p_col_top[1] + u[1] * 2.0 * scale + crescent_side * n[1] * 12.0 * scale,
        )
        p_crescent_mid_out = (
            p_col_top[0] + u[0] * 18.0 * scale + crescent_side * n[0] * 24.0 * scale,
            p_col_top[1] + u[1] * 18.0 * scale + crescent_side * n[1] * 24.0 * scale,
        )
        p_crescent_top = (
            p_col_top[0] + u[0] * 36.0 * scale + crescent_side * n[0] * 12.0 * scale,
            p_col_top[1] + u[0] * 36.0 * scale + crescent_side * n[1] * 12.0 * scale,
        )
        p_crescent_mid_in = (
            p_col_top[0] + u[0] * 18.0 * scale + crescent_side * n[0] * 14.0 * scale,
            p_col_top[1] + u[1] * 18.0 * scale + crescent_side * n[1] * 14.0 * scale,
        )
        poly_crescent = [p_crescent_bot, p_crescent_mid_out, p_crescent_top, p_crescent_mid_in]
        draw.polygon(poly_crescent, fill=(226, 232, 240, 255), outline=(45, 55, 72, 255))

        # 6. Tail butt cap
        p_tail_cap = (tail_pt.x - u[0] * 10.0 * scale, tail_pt.y - u[1] * 10.0 * scale)
        poly_tail = [
            (tail_pt.x - n[0] * w / 2.0, tail_pt.y - n[1] * w / 2.0),
            p_tail_cap,
            (tail_pt.x + n[0] * w / 2.0, tail_pt.y + n[1] * w / 2.0),
        ]
        draw.polygon(poly_tail, fill=(113, 128, 150, 255), outline=(45, 55, 72, 255))


def composite_character(
    body_renderer: HumanoidBodyRenderer,
    face_renderer: FaceFeatureRenderer,
    accessories_renderer: AccessoriesRenderer,
    character: StickmanCharacter,
    pose: StickmanPose,
    canvas_position: Point2D,
    facing: int = 1,
    canvas_size: tuple[int, int] = HumanoidBodyRenderer.DEFAULT_CANVAS_SIZE,
    weapon_renderer: Optional[WeaponRenderer] = None,
    align_two_hands: Optional[bool] = None,
    pose_def: Optional[PoseDefinition] = None,
    custom_angle_deg: Optional[float] = None,
    buddha_palm_renderer: Optional[BuddhaPalmRenderer] = None,
    palm_position: Optional[Point2D] = None,
    palm_scale: Optional[float] = None,
    palm_direction: str = "down",
    palm_descent_progress: float = 1.0,
    palm_layer_order: str = "foreground",
) -> Image.Image:
    """
    Composite a complete Dark Myth stickman character following strict layer order:

    1. Back accessories (Khăn choàng, Lông chim trĩ, Cloaks)
    2. Humanoid body skeleton (Bones, Joint caps, Head circle)
    3. Weapon layer (optional: Ruyi Staff, Three-Pointed Spear, Halberd)
    4. Facial features (Fiery eyes, Third Eye, Visor slits)
    5. Front accessories (Kim Cô, Helmets, Shoulder armor)
    6. Buddha Palm layer (if buddha_palm_renderer provided: "foreground", "background", or "weapon")

    Returns:
      Consolidated transparent RGBA PIL Image.
    """
    back_layer = accessories_renderer.render_back_accessories(
        character=character,
        pose=pose,
        canvas_position=canvas_position,
        facing=facing,
        canvas_size=canvas_size,
    )
    body_layer = body_renderer.render_body(
        character=character,
        pose=pose,
        canvas_position=canvas_position,
        facing=facing,
        canvas_size=canvas_size,
    )
    face_layer = face_renderer.render_face_features(
        character=character,
        pose=pose,
        canvas_position=canvas_position,
        facing=facing,
        canvas_size=canvas_size,
    )
    front_layer = accessories_renderer.render_front_accessories(
        character=character,
        pose=pose,
        canvas_position=canvas_position,
        facing=facing,
        canvas_size=canvas_size,
    )

    # Resolve Buddha Palm renderer: auto-activate if character is BUDDHA_PALM or GIANT_GOLDEN_PALM
    palm_ren = buddha_palm_renderer
    if palm_ren is None and (
        character.skin == CharacterSkin.BUDDHA_PALM
        or character.weapon == WeaponType.GIANT_GOLDEN_PALM
    ):
        palm_ren = weapon_renderer.get_buddha_palm_renderer() if weapon_renderer else BuddhaPalmRenderer()

    palm_layer = None
    should_render_palm = (
        character.skin == CharacterSkin.BUDDHA_PALM
        or character.weapon == WeaponType.GIANT_GOLDEN_PALM
        or palm_position is not None
    )
    if palm_ren is not None and should_render_palm:
        p_pos = palm_position or (
            canvas_position
            if character.skin == CharacterSkin.BUDDHA_PALM
            else Point2D(canvas_position.x, canvas_position.y - 300.0)
        )
        p_scale = palm_scale if palm_scale is not None else (
            character.scale
            if character.skin == CharacterSkin.BUDDHA_PALM
            else (character.scale * 3.5 if character.scale <= 1.5 else character.scale)
        )
        palm_layer = palm_ren.render_palm(
            position=p_pos,
            scale=p_scale,
            facing=facing,
            direction=palm_direction,
            descent_progress=palm_descent_progress,
            canvas_size=canvas_size,
        )

    # If the character itself is the Buddha Palm celestial entity, return the palm layer directly
    if character.skin == CharacterSkin.BUDDHA_PALM and palm_layer is not None:
        return palm_layer

    if palm_layer is not None and palm_layer_order == "background":
        composite = Image.alpha_composite(palm_layer, back_layer)
        composite = Image.alpha_composite(composite, body_layer)
    else:
        composite = Image.alpha_composite(back_layer, body_layer)

    if weapon_renderer is not None:
        weapon_layer = weapon_renderer.render_weapon(
            character=character,
            pose=pose,
            canvas_position=canvas_position,
            facing=facing,
            canvas_size=canvas_size,
            pose_def=pose_def,
            custom_angle_deg=custom_angle_deg,
            align_two_hands=align_two_hands,
        )
        composite = Image.alpha_composite(composite, weapon_layer)

    if palm_layer is not None and palm_layer_order == "weapon":
        composite = Image.alpha_composite(composite, palm_layer)

    composite = Image.alpha_composite(composite, face_layer)
    composite = Image.alpha_composite(composite, front_layer)

    if palm_layer is not None and palm_layer_order == "foreground":
        composite = Image.alpha_composite(composite, palm_layer)

    return composite
