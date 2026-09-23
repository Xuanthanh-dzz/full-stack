using DesignByContractDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static void Main(){

 var max=new StockItem("a",int.MaxValue);max.TryReserve(1,out _);Throws<OverflowException>(()=>max.Receive(1));Check(max.OnHand==int.MaxValue && max.Reserved==1,"overflow preserves state");
 var item=new StockItem("a",10);int hand=10,reserved=0;var random=new Random(12345);
 for(int i=0;i<1000;i++) {int q=random.Next(1,20);int op=random.Next(4);
  if(op==0){item.Receive(q);hand+=q;}
  else if(op==1){bool expected=q<=hand-reserved;Check(item.TryReserve(q,out _)==expected,"reserve result");if(expected)reserved+=q;}
  else if(op==2){if(q>reserved)Throws<InvalidOperationException>(()=>item.Ship(q));else{item.Ship(q);hand-=q;reserved-=q;}}
  else{if(q>reserved)Throws<InvalidOperationException>(()=>item.ReleaseReservation(q));else{item.ReleaseReservation(q);reserved-=q;}}
  Check(item.OnHand==hand && item.Reserved==reserved && item.Available==hand-reserved,"state model");
 }
 Check(!ReservationRequest.TryParse("","abc",out var request,out var errors) && request==null && errors.Count==2,"all validation errors");

 }

}
