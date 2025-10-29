"""数据模型：课表（基于线段树）、Teacher、Student。

课表采用离散化的时间槽（0..n-1），支持区间预订（[start, end)）和释放。
使用线段树保存覆盖计数（range add）与区间最大覆盖值（用于冲突检测）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


class SegmentTreeSchedule:
    """基于线段树的区间预订管理。

    - 初始化时指定槽数 n（时间被离散为 n 个单位，区间为 [0, n)）。
    - book(start, end): 当区间当前没有被占用（最大覆盖为 0）时，将该区间覆盖计数 +1 并返回 True；否则返回 False（不做修改）。
    - unbook(start, end): 将区间覆盖计数 -1（调用方需确保先前确实预订过）。
    - is_free(start, end): 返回区间是否未被占用（max == 0）。
    注意：实现以计数为基础，允许多次同一区间的重复预订（通过增加计数），但 `book` 默认阻止已有占用的插入。
    """

    def __init__(self, n: int):
        if n <= 0:
            raise ValueError("n must be positive")
        self.n = n
        self._size = 1
        while self._size < n:
            self._size <<= 1
        # 使用数组存储：lazy 为对该节点的累加，mx 为节点区间的最大覆盖
        self.lazy = [0] * (self._size * 2)
        self.mx = [0] * (self._size * 2)

    def _push(self, idx: int):
        # 将懒惰值下传给子节点
        v = self.lazy[idx]
        if v != 0:
            left = idx * 2
            right = left + 1
            self.lazy[left] += v
            self.lazy[right] += v
            self.mx[left] += v
            self.mx[right] += v
            self.lazy[idx] = 0

    def _range_add(self, ql: int, qr: int, val: int, idx: int, lx: int, rx: int):
        # 为区间 [ql, qr) 添加 val，当前节点 idx 覆盖区间 [lx, rx)
        if ql >= rx or qr <= lx:
            return
        if ql <= lx and rx <= qr:
            self.lazy[idx] += val
            self.mx[idx] += val
            return
        self._push(idx)
        mid = (lx + rx) // 2
        self._range_add(ql, qr, val, idx * 2, lx, mid)
        self._range_add(ql, qr, val, idx * 2 + 1, mid, rx)
        self.mx[idx] = max(self.mx[idx * 2], self.mx[idx * 2 + 1])

    def _range_max(self, ql: int, qr: int, idx: int, lx: int, rx: int) -> int:
        if ql >= rx or qr <= lx:
            return 0
        if ql <= lx and rx <= qr:
            return self.mx[idx]
        self._push(idx)
        mid = (lx + rx) // 2
        a = self._range_max(ql, qr, idx * 2, lx, mid)
        b = self._range_max(ql, qr, idx * 2 + 1, mid, rx)
        return max(a, b)

    def is_free(self, start: int, end: int) -> bool:
        self._check_bounds(start, end)
        return self._range_max(start, end, 1, 0, self._size) == 0

    def book(self, start: int, end: int) -> bool:
        """如果区间为空闲则预订并返回 True，否则返回 False（不修改）。"""
        self._check_bounds(start, end)
        if self.is_free(start, end):
            self._range_add(start, end, 1, 1, 0, self._size)
            return True
        return False

    def force_book(self, start: int, end: int) -> None:
        """不做冲突检测，直接将区间覆盖计数 +1。"""
        self._check_bounds(start, end)
        self._range_add(start, end, 1, 1, 0, self._size)

    def unbook(self, start: int, end: int) -> None:
        """将区间覆盖计数 -1（调用方需保证此前已成功预订）。"""
        self._check_bounds(start, end)
        self._range_add(start, end, -1, 1, 0, self._size)

    def _check_bounds(self, start: int, end: int) -> None:
        if not (0 <= start < end <= self.n):
            raise ValueError(f"invalid interval [{start}, {end}) for size {self.n}")

    def __repr__(self) -> str:
        return f"SegmentTreeSchedule(n={self.n})"


@dataclass
class Teacher:
    id: int
    name: str
    email: Optional[str] = None
    # 保存该教师的个人预订记录：列表包含 (start, end, course_id)
    bookings: List[Tuple[int, int, Optional[int]]] = field(default_factory=list)

    def assign_slot(self, schedule: SegmentTreeSchedule, start: int, end: int, course_id: Optional[int] = None) -> bool:
        """尝试在给定 schedule 为教师分配时间段；成功则记录并返回 True。"""
        ok = schedule.book(start, end)
        if ok:
            self.bookings.append((start, end, course_id))
        return ok

    def release_slot(self, schedule: SegmentTreeSchedule, start: int, end: int) -> None:
        schedule.unbook(start, end)
        # 移除所有匹配的 bookings（若部分重叠或重复请按业务调整）
        self.bookings = [b for b in self.bookings if not (b[0] == start and b[1] == end)]


@dataclass
class Student:
    id: int
    name: str
    email: Optional[str] = None
    # 学生选课记录：(course_id, start, end)
    enrollments: List[Tuple[int, int, int]] = field(default_factory=list)

    def enroll(self, schedule: SegmentTreeSchedule, course_id: int, start: int, end: int) -> bool:
        """如果时间段可用则为学生选课（占用该时段）并记录报名。"""
        ok = schedule.book(start, end)
        if ok:
            self.enrollments.append((course_id, start, end))
        return ok

    def drop(self, schedule: SegmentTreeSchedule, course_id: int, start: int, end: int) -> None:
        schedule.unbook(start, end)
        self.enrollments = [e for e in self.enrollments if not (e[0] == course_id and e[1] == start and e[2] == end)]


__all__ = ["SegmentTreeSchedule", "Teacher", "Student"]
