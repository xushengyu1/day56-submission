"""
身份证全链路端到端测试脚本。

流程：
  1. 用户1（张明）招领：创建拾到记录 → 上传图片 → AI提取 → 确认身份信息 → 脱敏 → 发布
  2. 用户2（李婷）寻物：创建丢失记录 → 触发匹配 → 查看候选 → 提交认领
  3. 验证认领结果

用法：
    python -m scripts.test_id_flow
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"
BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = BACKEND_ROOT.parents[1]
IMAGE_PATH = REPOSITORY_ROOT / "images" / "身份证.jpeg"

# 身份证号码（测试用假号码，18位）
TEST_ID_NUMBER = "110101199003071233"


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # ============================================================
        # 步骤 0：注册/登录两个用户
        # ============================================================
        print("=" * 60)
        print("步骤 0：登录用户")
        print("=" * 60)

        # 登录张明（招领者）
        resp = await client.post("/api/auth/login", json={
            "email": "zhangming@example.test",
            "password": "Xiaoming123!",
        })
        if resp.status_code != 200:
            print(f"[错误] 张明登录失败: {resp.status_code} {resp.text}")
            sys.exit(1)
        zhang_token = resp.json()["tokens"]["access_token"]
        zhang_headers = {"Authorization": f"Bearer {zhang_token}"}
        print(f"  张明登录成功")

        # 登录李婷（失主）
        resp = await client.post("/api/auth/login", json={
            "email": "liting@example.test",
            "password": "Xiaoming123!",
        })
        if resp.status_code != 200:
            print(f"[错误] 李婷登录失败: {resp.status_code} {resp.text}")
            sys.exit(1)
        li_token = resp.json()["tokens"]["access_token"]
        li_headers = {"Authorization": f"Bearer {li_token}"}
        print(f"  李婷登录成功")

        # ============================================================
        # 步骤 1：张明创建拾到记录（招领）
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 1：张明创建拾到记录（招领）")
        print("=" * 60)

        now = datetime.now(timezone.utc)
        resp = await client.post("/api/found-records", json={
            "event_time": (now - timedelta(hours=2)).isoformat(),
            "location_area": "CANTEEN",
        }, headers=zhang_headers)
        if resp.status_code != 201:
            print(f"[错误] 创建拾到记录失败: {resp.status_code} {resp.text}")
            sys.exit(1)
        foundRecord = resp.json()
        found_record_id = foundRecord["id"]
        found_version = foundRecord["version"]
        print(f"  拾到记录创建成功: ID={found_record_id}, 版本={found_version}")

        # ============================================================
        # 步骤 2：上传身份证图片
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 2：上传身份证图片")
        print("=" * 60)

        if not IMAGE_PATH.exists():
            print(f"[错误] 图片不存在: {IMAGE_PATH}")
            sys.exit(1)

        image_data = IMAGE_PATH.read_bytes()
        resp = await client.post("/api/uploads", headers=zhang_headers, files={
            "file": ("身份证.jpeg", image_data, "image/jpeg"),
        }, data={
            "record_id": found_record_id,
            "purpose": "FINDER_ORIGINAL",
        })
        if resp.status_code != 201:
            print(f"[错误] 上传图片失败: {resp.status_code} {resp.text}")
            sys.exit(1)
        uploadResult = resp.json()
        image_asset_id = uploadResult["image_asset_id"]
        print(f"  图片上传成功: asset_id={image_asset_id}")

        # ============================================================
        # 步骤 3：AI 提取识别
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 3：AI 提取识别")
        print("=" * 60)

        resp = await client.post(
            f"/api/found-records/{found_record_id}/extract",
            json={"image_asset_id": image_asset_id},
            headers=zhang_headers,
        )
        if resp.status_code != 200:
            print(f"[错误] AI提取失败: {resp.status_code} {resp.text}")
            sys.exit(1)
        extraction = resp.json()
        print(f"  AI提取成功:")
        print(f"    建议名称: {extraction['suggested_name']}")
        print(f"    建议描述: {extraction['suggested_description']}")
        print(f"    建议类型: {extraction['suggested_item_type']}")
        print(f"    置信度:   {extraction['confidence']}")

        # ============================================================
        # 步骤 3.5：确认草稿（设置分类为身份证）
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 3.5：确认草稿（设置分类为身份证）")
        print("=" * 60)

        event_time_str = (now - timedelta(hours=2)).isoformat()
        resp = await client.put(
            f"/api/found-records/{found_record_id}/confirmation",
            json={
                "expected_version": found_version,
                "public_category": "IDENTITY_CARD",
                "name_public": extraction["suggested_name"],
                "description_public": extraction["suggested_description"],
                "event_time": event_time_str,
                "location_area": "CANTEEN",
            },
            headers=zhang_headers,
        )
        if resp.status_code != 200:
            print(f"[错误] 确认草稿失败: {resp.status_code} {resp.text}")
            sys.exit(1)
        confirmResult = resp.json()
        found_version = confirmResult["version"]
        print(f"  草稿确认成功: 版本={found_version}")

        # ============================================================
        # 步骤 4：确认身份信息（输入身份证号码）
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 4：确认身份信息（输入身份证号码）")
        print("=" * 60)

        resp = await client.post(
            f"/api/found-records/{found_record_id}/identity-confirmation",
            json={
                "full_number": TEST_ID_NUMBER,
                "digits_confirmed": True,
            },
            headers=zhang_headers,
        )
        if resp.status_code != 200:
            print(f"[错误] 确认身份信息失败: {resp.status_code} {resp.text}")
            sys.exit(1)
        identityResult = resp.json()
        print(f"  身份信息确认成功:")
        print(f"    脱敏号码: {identityResult['number_masked']}")

        # ============================================================
        # 步骤 5：创建脱敏公开图片
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 5：创建脱敏公开图片")
        print("=" * 60)

        resp = await client.post(
            f"/api/found-records/{found_record_id}/redaction",
            json={
                "original_asset_id": image_asset_id,
                "region": {
                    "x": 60, "y": 60,
                    "width": 680, "height": 380,
                },
            },
            headers=zhang_headers,
        )
        if resp.status_code != 201:
            print(f"[错误] 创建脱敏图片失败: {resp.status_code} {resp.text}")
            sys.exit(1)
        redactionResult = resp.json()
        print(f"  脱敏图片创建成功: asset_id={redactionResult['asset_id']}, 状态={redactionResult['status']}")

        # ============================================================
        # 步骤 6：发布拾到记录
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 6：发布拾到记录")
        print("=" * 60)

        resp = await client.post(
            f"/api/found-records/{found_record_id}/publish",
            json={"expected_version": found_version},
            headers=zhang_headers,
        )
        if resp.status_code != 200:
            print(f"[错误] 发布失败: {resp.status_code} {resp.text}")
            sys.exit(1)
        publishResult = resp.json()
        print(f"  发布成功: 状态={publishResult['status']}, 版本={publishResult['version']}")

        # ============================================================
        # 步骤 7：李婷创建丢失记录（寻物）
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 7：李婷创建丢失记录（寻物）")
        print("=" * 60)

        resp = await client.post("/api/lost-records", json={
            "public_category": "IDENTITY_CARD",
            "location_area": "CANTEEN",
            "event_time": (now - timedelta(hours=3)).isoformat(),
            "name_public": "居民身份证",
            "description_public": "蓝色居民身份证，装在透明卡套中，在一食堂丢失。",
        }, headers=li_headers)
        if resp.status_code != 201:
            print(f"[错误] 创建丢失记录失败: {resp.status_code} {resp.text}")
            sys.exit(1)
        lostResult = resp.json()
        lost_record_id = lostResult["id"]
        print(f"  丢失记录创建成功: ID={lost_record_id}, 状态={lostResult['status']}")

        # ============================================================
        # 步骤 8：触发匹配（SSE 流）
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 8：触发匹配")
        print("=" * 60)

        async with client.stream(
            "GET",
            f"/api/lost-records/{lost_record_id}/match",
            headers=li_headers,
        ) as resp:
            if resp.status_code != 200:
                body = await resp.aread()
                print(f"[错误] 匹配请求失败: {resp.status_code} {body.decode()}")
                sys.exit(1)
            async for line in resp.aiter_lines():
                if line.startswith("event:"):
                    event_type = line.split(":", 1)[1].strip()
                elif line.startswith("data:"):
                    import json
                    data = json.loads(line.split(":", 1)[1].strip())
                    if event_type == "progress":
                        print(f"  匹配进度: {data['stage']} - {data['progress']}%")
                    elif event_type == "done":
                        print(f"  匹配完成!")
                    elif event_type == "error":
                        print(f"  [错误] 匹配失败: {data}")

        # ============================================================
        # 步骤 9：查看候选匹配
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 9：查看候选匹配")
        print("=" * 60)

        resp = await client.get(
            f"/api/lost-records/{lost_record_id}/candidates",
            headers=li_headers,
        )
        if resp.status_code != 200:
            print(f"[错误] 获取候选失败: {resp.status_code} {resp.text}")
            sys.exit(1)
        candidates = resp.json()
        print(f"  找到 {len(candidates)} 个候选匹配:")
        for c in candidates:
            print(f"    - 候选ID: {c['id']}")
            print(f"      总分: {c['total_score']}, 级别: {c['level']}")
            print(f"      匹配原因: {c['reason_codes']}")
            print(f"      冲突: {c['conflict_codes']}")
            print(f"      拾到记录: {c['found_record']['id']}")
            print(f"      拾到描述: {c['found_record']['description_public']}")

        if not candidates:
            print("[警告] 没有找到候选匹配，流程终止")
            sys.exit(1)

        candidate_id = candidates[0]["id"]

        # ============================================================
        # 步骤 10：李婷提交身份认领
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 10：李婷提交身份认领（输入身份证号码）")
        print("=" * 60)

        resp = await client.post(
            f"/api/candidates/{candidate_id}/claims/identity",
            json={"full_number": TEST_ID_NUMBER},
            headers=li_headers,
        )
        if resp.status_code != 200:
            print(f"[错误] 提交认领失败: {resp.status_code} {resp.text}")
            sys.exit(1)
        claimResult = resp.json()
        print(f"  认领提交成功:")
        print(f"    认领ID: {claimResult['claim_id']}")
        print(f"    状态:   {claimResult['status']}")
        print(f"    结果:   {claimResult['result_code']}")
        print(f"    尝试次数: {claimResult['attempt_no']}")
        print(f"    剩余次数: {claimResult['attempts_remaining']}")

        # ============================================================
        # 步骤 11：查看认领详情
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 11：查看认领详情")
        print("=" * 60)

        claim_id = claimResult["claim_id"]
        resp = await client.get(
            f"/api/claims/{claim_id}",
            headers=li_headers,
        )
        if resp.status_code != 200:
            print(f"[错误] 获取认领详情失败: {resp.status_code} {resp.text}")
            sys.exit(1)
        claimDetail = resp.json()
        print(f"  认领详情:")
        print(f"    认领ID: {claimDetail['id']}")
        print(f"    状态:   {claimDetail['status']}")
        print(f"    物品类型: {claimDetail['item_type']}")
        print(f"    来源:   {claimDetail['route_source']}")
        print(f"    原因:   {claimDetail.get('final_reason', '无')}")

        # ============================================================
        # 步骤 12：查看拾到记录详情（验证状态一致）
        # ============================================================
        print("\n" + "=" * 60)
        print("步骤 12：验证记录状态一致性")
        print("=" * 60)

        # 查看拾到记录
        resp = await client.get(
            f"/api/found-records/{found_record_id}",
            headers=zhang_headers,
        )
        if resp.status_code == 200:
            foundDetail = resp.json()
            print(f"  拾到记录状态: {foundDetail['status']}")
            print(f"  拾到记录脱敏号码: {foundDetail.get('number_masked', '无')}")

        # 查看丢失记录
        resp = await client.get(
            f"/api/lost-records/{lost_record_id}",
            headers=li_headers,
        )
        if resp.status_code == 200:
            lostDetail = resp.json()
            print(f"  丢失记录状态: {lostDetail['status']}")

        # ============================================================
        # 总结
        # ============================================================
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        print(f"  拾到记录 ID: {found_record_id}")
        print(f"  丢失记录 ID: {lost_record_id}")
        print(f"  认领记录 ID: {claim_id}")
        print(f"  认领状态: {claimResult['status']}")
        print(f"  认领结果: {claimResult['result_code']}")

        if claimResult["result_code"] == "IDENTITY_VERIFIED":
            print("\n  [通过] 身份证全链路测试通过！")
        elif claimResult["result_code"] == "DUPLICATE_IDENTITY_REVIEW":
            print("\n  [警告] 身份验证通过，但需要管理员审核（存在重复身份）")
        else:
            print(f"\n  [失败] 认领结果异常: {claimResult['result_code']}")


if __name__ == "__main__":
    asyncio.run(main())
