Electronic Data Interchange for Products
========================================

EDI capability for the Odoo ```product``` module.

Key Features
------------
* Quickly import product lists from external EDI sources
* Automatic deduplication of unmodified product records
* Easily customisable to handle new or custom document formats

Information
-----------
#. 依赖第三方模块 `edi_product <https://github.com/unipartdigital/odoo-edi/tree/master/addons/edi_product>`_ 。
#. 配合定制模块 *product_newbiiz* 。
#. 以2018年10月15日 *odoo_products_20181015.csv* [1]_ 作为解析对象。

   能处理的CSV文件其字段包含

   * name
   * Ma Labs List #
   * item_no
   * barcode
   * Mfr Part #
   * Manufacturer
   * Package
   * Unit
   * weight
   * width
   * height
   * Length
   * Sales Price
   * Cost
   * Instant Rebate
   * Instant Rebate Start [2]_
   * Instant Rebate End [3]_
   * website_description
   * image

   字段顺序没有要求。
#. *EDI* → *Configuration* → *Document Types* 将增加一项： *Product Ma Labs CAD*

   新增 *EDI Documents* 的时，可作为"Document Type"的选项。

.. [1] SHA512:

       2efc30350171aeb896cb52569d584c32f699cb615690d091857184a2c5c410a00cdad56fbbacec93cfc33dc83e95aa62be1778e1e4d744db50f3f7fdaa9a9588
.. [2] 表示日期时间的字符串(YYYY-MM-DD HH:mm:ss)，如果字符串不能解析用当前时间代替。
.. [3] 表示日期时间的字符串(YYYY-MM-DD HH:mm:ss)，如果字符串不能解析用”Instant Rebate End“的30日后。