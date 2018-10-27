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
#. 依赖第三方模块 `edi <https://github.com/unipartdigital/odoo-edi>`_ 。
#. 配合定制模块 *product_newbiiz* 。
#. 以2018年5月31日Olivia邮件附件 *odoo_products_20180525.csv* 作为解析对象。

   能处理的CSV文件其字段包含

   * name
   * Ma Labs List #
   * item_no
   * barcode
   * Mfr Part #
   * Manufacturer
   * Package
   * Unit
   * weight [1]_
   * width [2]_
   * height [2]_
   * Length [2]_
   * Sales Price [3]_
   * Cost [3]_
   * Instant Rebate
   * Instant Rebate Start [4]_
   * Instant Rebate End [5]_
   * website_description
   * image

   字段顺序没有要求。
#. *EDI* → *Configuration* → *Document Types* 将增加一项： *Product Ma Labs CAD*

   新增 *EDI Documents* 的时，可作为"Document Type"的选项。

.. [1] 单位：磅（lbs），换算成千克（KG）
.. [2] 单位：英吋（inch），换算成厘米（cm）
.. [3] 单位：美元（USD），换算成加币（CAD）
.. [4] 表示日期时间的字符串(YYYY-MM-DD HH:mm:ss)，如果字符串不能解析用当前时间代替。
.. [5] 表示日期时间的字符串(YYYY-MM-DD HH:mm:ss)，如果字符串不能解析用”Instant Rebate End“的30日后。