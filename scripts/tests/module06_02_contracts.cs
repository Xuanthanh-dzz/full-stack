using OopPillarsDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static void Main(){

 var wallet=new StoreCredit("a");wallet.Deposit(100);Check(wallet.TryPay(40,out _),"pay");var view=wallet.History;
 Check(!wallet.TryPay(90,out _) && wallet.Balance==60 && view.Count==2,"failure no history or balance change");
 Throws<NotSupportedException>(()=>((ICollection<string>)view).Clear());Throws<ArgumentOutOfRangeException>(()=>wallet.Deposit(0));
 var r=new Receipt("A","N",new[]{new ReceiptLine("X",2,6)},6);
 IReceiptFormatter text=new TextReceiptFormatter(),csv=new CsvReceiptFormatter();
 Check(text.Format(r).Contains("X x2 = 6") && csv.Format(r).Contains("X,2,6"),"dispatch");Throws<ArgumentNullException>(()=>text.Format(null!));

 }

}
