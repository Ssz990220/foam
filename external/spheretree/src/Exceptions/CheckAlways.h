/*************************************************************************\

                             C O P Y R I G H T

  Copyright 2003 Image Synthesis Group, Trinity College Dublin, Ireland.
                        All Rights Reserved.

  Permission to use, copy, modify and distribute this software and its
  documentation for educational, research and non-profit purposes, without
  fee, and without a written agreement is hereby granted, provided that the
  above copyright notice and the following paragraphs appear in all copies.


                             D I S C L A I M E R

  IN NO EVENT SHALL TRININTY COLLEGE DUBLIN BE LIABLE TO ANY PARTY FOR 
  DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING,
  BUT NOT LIMITED TO, LOST PROFITS, ARISING OUT OF THE USE OF THIS SOFTWARE 
  AND ITS DOCUMENTATION, EVEN IF TRINITY COLLEGE DUBLIN HAS BEEN ADVISED OF 
  THE POSSIBILITY OF SUCH DAMAGES.

  TRINITY COLLEGE DUBLIN DISCLAIM ANY WARRANTIES, INCLUDING, BUT NOT LIMITED 
  TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
  PURPOSE.  THE SOFTWARE PROVIDED HEREIN IS ON AN "AS IS" BASIS, AND TRINITY 
  COLLEGE DUBLIN HAS NO OBLIGATIONS TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
  ENHANCEMENTS, OR MODIFICATIONS.

  The authors may be contacted at the following e-mail addresses:

          Gareth_Bradshaw@yahoo.co.uk    isg@cs.tcd.ie

  Further information about the ISG and it's project can be found at the ISG
  web site :

          isg.cs.tcd.ie

\**************************************************************************/

/*
    Macros to check condition during both debug and release

    CHECK_DEBUGn takes n parameters to the message
*/
#ifndef _CHECK_ALWAYS_H_
#define _CHECK_ALWAYS_H_

#include "Exception.h"
#include "ErrorLog.h"

#define CHECK_ALWAYS0(cond) \
                                if (!(cond)){  \
                                  writeErrorLog(#cond, __FILE__, __LINE__, NULL); \
                                  throw new Exception(#cond, __FILE__, __LINE__); \
                                  }

#define CHECK_ALWAYS(cond, msg) \
                                if (!(cond)){  \
                                  writeErrorLog(#cond, __FILE__, __LINE__, msg); \
                                  throw new Exception(#cond, __FILE__, __LINE__); \
                                  }

#define CHECK_ALWAYS1(cond, msg, a) \
                                if (!(cond)){  \
                                  writeErrorLog(#cond, __FILE__, __LINE__, msg, a); \
                                  throw new Exception(#cond, __FILE__, __LINE__); \
                                  }

#define CHECK_ALWAYS2(cond, msg, a, b) \
                                if (!(cond)){  \
                                  writeErrorLog(#cond, __FILE__, __LINE__, msg, a, b); \
                                  throw new Exception(#cond, __FILE__, __LINE__); \
                                  }

#define CHECK_ALWAYS3(cond, msg, a, b, c) \
                                if (!(cond)){  \
                                  writeErrorLog(#cond, __FILE__, __LINE__, msg, a, b, c); \
                                  throw new Exception(#cond, __FILE__, __LINE__); \
                                  }

#define CHECK_ALWAYS4(cond, msg, a, b, c, d) \
                                if (!(cond)){  \
                                  writeErrorLog(#cond, __FILE__, __LINE__, msg, a, b, c, d); \
                                  throw new Exception(#cond, __FILE__, __LINE__); \
                                  }

#endif