=======
History
=======

0.7.0 (2023-08-10)
------------------
* Call convert_value on underlying expression if available.

0.5.4 (2022-09-22)
------------------
* Allow using a shared_property as a target of an OuterRef in a Subquery/Exists.

0.5.3 (2022-09-15)
------------------
* Really support abstract models - actually querying was not working.

0.5.2 (2022-09-09)
------------------
* Support using a shared_property on an abstract base model.

0.5.1 (2022-09-05)
------------------
* Bugfix for supporting chained lookups.

0.5.0 (2022-09-03)
------------------
* Support queries over joined models.

0.4.0 (2022-08-30)
------------------
* Support Django 4.1
* Handle writing values to shared_property fields (ie, refetch from db, etc).

0.3.0 (2022-03-18)
------------------
* Support Django 4.0
* Implement Coalesce and CombinedExpression
* Support pluggable handlers.



0.2.6 (2021-07-29)
------------------

* Remove unused dependency.

0.2.5 (2021-07-26)
------------------

* Fixed bug with complex queries.

0.2.4 (2021-07-23)
------------------

* Fix bug with output_field

0.2.3 (2021-07-23)
------------------

* Ensure tables are referenced.

0.2.2 (2021-07-22)
------------------

* Remove debugging statements

0.2.1 (2021-07-22)
------------------

* Fix to allow installing

0.2.0 (2021-07-22)
------------------

* Support Enum return values.
* Simplify decorator code.


0.1.0 (2020-09-15)
------------------

* First release on PyPI.
