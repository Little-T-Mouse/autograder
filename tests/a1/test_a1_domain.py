"""Fresh practice tests on parcel, truck and fleet edge cases."""
import pytest


def test_parcel_fields_are_recorded():
    from domain import Parcel
    package = Parcel(901, 7, 'North', 'South')
    assert (package.id_, package.volume, package.source, package.destination) == (
        901, 7, 'North', 'South'
    )


def test_truck_initially_empty_at_depot():
    from domain import Truck
    vehicle = Truck(21, 16, 'Base')
    assert vehicle.used_space == 0
    assert vehicle.route == ['Base']
    assert vehicle.parcel == []
    assert vehicle.fullness() == 0.0


def test_truck_allows_exact_capacity():
    from domain import Parcel, Truck
    vehicle = Truck(21, 12, 'Base')
    assert vehicle.pack(Parcel(2, 7, 'Elsewhere', 'Oak')) is True
    assert vehicle.pack(Parcel(3, 5, 'Elsewhere', 'Pine')) is True
    assert vehicle.used_space == 12
    assert vehicle.fullness() == 100.0
    assert vehicle.route == ['Base', 'Oak', 'Pine']


def test_truck_rejects_oversize_without_changes():
    from domain import Parcel, Truck
    vehicle = Truck(21, 11, 'Base')
    assert vehicle.pack(Parcel(2, 8, 'Other', 'Oak'))
    before = (vehicle.used_space, vehicle.route[:], vehicle.parcel[:])
    assert vehicle.pack(Parcel(3, 4, 'Other', 'Pine')) is False
    assert (vehicle.used_space, vehicle.route, vehicle.parcel) == before


def test_truck_does_not_duplicate_consecutive_stop():
    from domain import Parcel, Truck
    vehicle = Truck(21, 30, 'Base')
    assert vehicle.pack(Parcel(2, 3, 'North', 'Oak'))
    assert vehicle.pack(Parcel(3, 4, 'North', 'Oak'))
    assert vehicle.pack(Parcel(4, 5, 'North', 'Elm'))
    assert vehicle.route == ['Base', 'Oak', 'Elm']
    assert [p.id_ for p in vehicle.parcel] == [2, 3, 4]


def test_fleet_allocations_include_empty_truck():
    from domain import Fleet, Parcel, Truck
    fleet = Fleet()
    first = Truck(17, 20, 'Base')
    second = Truck(18, 20, 'Base')
    first.pack(Parcel(35, 6, 'A', 'Oak'))
    fleet.add_truck(first)
    fleet.add_truck(second)
    assert fleet.num_trucks() == 2
    assert fleet.num_nonempty_trucks() == 1
    assert fleet.parcel_allocations() == {17: [35], 18: []}


def test_fleet_unused_capacity_counts_only_used_trucks():
    from domain import Fleet, Parcel, Truck
    fleet = Fleet()
    loaded = Truck(1, 25, 'Base')
    empty = Truck(2, 1000, 'Base')
    loaded.pack(Parcel(1, 6, 'A', 'Oak'))
    fleet.add_truck(loaded)
    fleet.add_truck(empty)
    assert fleet.total_unused_space() == 19
    assert fleet.average_fullness() == pytest.approx(24)


def test_fleet_distance_includes_return_and_excludes_idle_vehicles():
    from distance_map import DistanceMap
    from domain import Fleet, Parcel, Truck
    fleet = Fleet()
    busy = Truck(3, 20, 'Base')
    idle = Truck(4, 20, 'Base')
    busy.pack(Parcel(6, 7, 'A', 'Oak'))
    busy.pack(Parcel(7, 5, 'A', 'Elm'))
    fleet.add_truck(busy)
    fleet.add_truck(idle)
    distances = DistanceMap()
    distances.add_distance('Base', 'Oak', 5)
    distances.add_distance('Oak', 'Elm', 7)
    distances.add_distance('Elm', 'Base', 11)
    assert fleet.total_distance_travelled(distances) == 23
    assert fleet.average_distance_travelled(distances) == pytest.approx(23)


def test_fleet_average_uses_only_active_trucks():
    from domain import Fleet, Parcel, Truck
    fleet = Fleet()
    for number, used in [(51, 4), (52, 8), (53, 0)]:
        vehicle = Truck(number, 20, 'Base')
        if used:
            vehicle.pack(Parcel(number, used, 'Other', 'Oak'))
        fleet.add_truck(vehicle)
    assert fleet.average_fullness() == pytest.approx(30.0)
    assert fleet.total_unused_space() == 28
